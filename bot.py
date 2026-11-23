"""
Veille de stages en finance : interroge LinkedIn (et en option des sites
Workday / SmartRecruiters), filtre selon config.yaml et envoie chaque
NOUVELLE offre sur Telegram. Les offres déjà vues sont stockées dans
state/seen.json pour ne jamais être renvoyées.
"""

import html
import json
import os
import random
import re
import sys
import time
import unicodedata
from datetime import datetime, timedelta, timezone
from pathlib import Path
from urllib.parse import urlparse

import requests
import yaml
from bs4 import BeautifulSoup

ROOT = Path(__file__).parent
STATE_FILE = ROOT / "state" / "seen.json"
CONFIG_FILE = ROOT / "config.yaml"

UA = ("Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
      "(KHTML, like Gecko) Chrome/124.0 Safari/537.36")
HEADERS = {"User-Agent": UA, "Accept-Language": "fr-FR,fr;q=0.9,en;q=0.8"}

SEEN_RETENTION_DAYS = 60       # on oublie les offres vues il y a plus de 60 j
FAIL_ALERT_EVERY = 6           # alerte si 6 passages d'affilée échouent
FIRST_RUN_MAX_SENT = 15        # au tout premier passage, on n'envoie que 15 offres max


# ---------------------------------------------------------------- utilitaires
def norm(text: str) -> str:
    """minuscules + suppression des accents, pour comparer les mots-clés."""
    text = unicodedata.normalize("NFKD", text or "")
    text = "".join(c for c in text if not unicodedata.combining(c))
    return re.sub(r"\s+", " ", text.lower()).strip()


def contains_any(text: str, terms) -> bool:
    t = norm(text)
    for term in terms:
        term_n = norm(term)
        # mots courts (alm, cdi...) : on exige un mot entier
        # mot court (alm, cdi...) ou terme finissant par "!" : mot entier exigé
        # sinon : le mot doit COMMENCER par le terme (liquidit -> liquidité)
        whole = len(term_n) <= 4 or term_n.endswith("!")
        term_n = term_n.rstrip("!")
        pattern = rf"\b{re.escape(term_n)}" + (r"\b" if whole else "")
        if re.search(pattern, t):
            return True
    return False


def is_vie(title: str) -> bool:
    # "VIE" en majuscules ou "V.I.E" = Volontariat International, pas un stage
    return bool(re.search(r"\bV\.?I\.?E\b", title)) and "assurance" not in norm(title)


def load_state() -> dict:
    if STATE_FILE.exists():
        try:
            return json.loads(STATE_FILE.read_text(encoding="utf-8"))
        except json.JSONDecodeError:
            pass
    return {"seen": {}, "consecutive_failures": 0, "last_heartbeat": ""}


def save_state(state: dict) -> None:
    STATE_FILE.parent.mkdir(parents=True, exist_ok=True)
    STATE_FILE.write_text(json.dumps(state, ensure_ascii=False, indent=1, sort_keys=True),
                          encoding="utf-8")


def polite_sleep():
    time.sleep(random.uniform(1.5, 3.5))


# ---------------------------------------------------------------- sources
def fetch_linkedin(cfg: dict) -> tuple[list, int, int]:
    """Renvoie (offres, nb_requêtes_ok, nb_requêtes_ko)."""
    jobs, ok, ko = [], 0, 0
    max_age = int(cfg.get("max_age_hours", 24)) * 3600
    base = "https://www.linkedin.com/jobs-guest/jobs/api/seeMoreJobPostings/search"
    for kw in cfg.get("keywords", []):
        for loc in cfg.get("locations", []):
            params = {
                "keywords": kw,
                "location": loc,
                "f_JT": "I",            # type de contrat : stage
                "f_E": "1",             # niveau d'expérience : stage
                "f_TPR": f"r{max_age}",  # publié depuis moins de X secondes
                "sortBy": "DD",         # plus récentes d'abord
                "start": 0,
            }
            try:
                r = requests.get(base, params=params, headers=HEADERS, timeout=20)
                if r.status_code == 429:
                    print("[linkedin] 429 trop de requêtes, on arrête LinkedIn pour ce passage")
                    ko += 1
                    return jobs, ok, ko
                r.raise_for_status()
                ok += 1
            except requests.RequestException as e:
                print(f"[linkedin] erreur {kw!r} / {loc!r} : {e}")
                ko += 1
                polite_sleep()
                continue

            soup = BeautifulSoup(r.text, "html.parser")
            for card in soup.select("div.base-card, div.job-search-card"):
                urn = card.get("data-entity-urn", "")
                m = re.search(r"(\d+)$", urn)
                if not m:
                    a = card.select_one("a.base-card__full-link")
                    m = re.search(r"-(\d+)(?:\?|$)", a["href"]) if a and a.get("href") else None
                if not m:
                    continue
                job_id = m.group(1)
                title = card.select_one(".base-search-card__title")
                company = card.select_one(".base-search-card__subtitle")
                location = card.select_one(".job-search-card__location")
                posted = card.select_one("time")
                jobs.append({
                    "key": f"li:{job_id}",
                    "source": "LinkedIn",
                    "title": title.get_text(strip=True) if title else "",
                    "company": company.get_text(strip=True) if company else "",
                    "location": location.get_text(strip=True) if location else "",
                    "posted": (posted.get("datetime") if posted else "") or "",
                    "posted_label": posted.get_text(strip=True) if posted else "",
                    "url": f"https://www.linkedin.com/jobs/view/{job_id}",
                    "is_internship_source": True,
                })
            polite_sleep()
    return jobs, ok, ko


def fetch_workday(cfg: dict) -> tuple[list, int, int]:
    jobs, ok, ko = [], 0, 0
    for site in cfg.get("sites", []) or []:
        url = site.get("url", "").rstrip("/")
        p = urlparse(url)
        host = p.netloc
        parts = [s for s in p.path.split("/") if s and not re.fullmatch(r"[a-z]{2}-[A-Z]{2}", s)]
        if not host or not parts:
            print(f"[workday] URL invalide : {url}")
            ko += 1
            continue
        tenant, site_name = host.split(".")[0], parts[0]
        api = f"https://{host}/wday/cxs/{tenant}/{site_name}/jobs"
        for term in cfg.get("search_terms", ["intern"]):
            try:
                r = requests.post(api, json={"appliedFacets": {}, "limit": 20, "offset": 0,
                                             "searchText": term},
                                  headers={**HEADERS, "Content-Type": "application/json"},
                                  timeout=20)
                r.raise_for_status()
                ok += 1
            except requests.RequestException as e:
                print(f"[workday] {site.get('name')} erreur : {e}")
                ko += 1
                continue
            for jp in r.json().get("jobPostings", []):
                path = jp.get("externalPath", "")
                jobs.append({
                    "key": f"wd:{host}:{path}",
                    "source": site.get("name", tenant),
                    "title": jp.get("title", ""),
                    "company": site.get("name", tenant),
                    "location": jp.get("locationsText", ""),
                    "posted": "",
                    "posted_label": jp.get("postedOn", ""),
                    "url": f"https://{host}/{site_name}{path}",
                    "is_internship_source": False,
                })
            polite_sleep()
    return jobs, ok, ko


def fetch_smartrecruiters(cfg: dict) -> tuple[list, int, int]:
    jobs, ok, ko = [], 0, 0
    for comp in cfg.get("companies", []) or []:
        cid = comp.get("id")
        for term in cfg.get("search_terms", ["intern"]):
            try:
                r = requests.get(f"https://api.smartrecruiters.com/v1/companies/{cid}/postings",
                                 params={"q": term, "limit": 100}, headers=HEADERS, timeout=20)
                r.raise_for_status()
                ok += 1
            except requests.RequestException as e:
                print(f"[smartrecruiters] {cid} erreur : {e}")
                ko += 1
                continue
            for jp in r.json().get("content", []):
                loc = jp.get("location", {}) or {}
                jobs.append({
                    "key": f"sr:{cid}:{jp.get('id')}",
                    "source": comp.get("name", cid),
                    "title": jp.get("name", ""),
                    "company": (jp.get("company") or {}).get("name", comp.get("name", cid)),
                    "location": ", ".join(x for x in [loc.get("city"), loc.get("country")] if x),
                    "posted": jp.get("releasedDate", ""),
                    "posted_label": "",
                    "url": f"https://jobs.smartrecruiters.com/{cid}/{jp.get('id')}",
                    "is_internship_source": False,
                })
            polite_sleep()
    return jobs, ok, ko


def fetch_talentsoft(cfg: dict) -> tuple[list, int, int]:
    """Sites carrières du groupe Crédit Agricole (Amundi, CACEIS, Indosuez...) :
    ils publient un flux RSS des 20 dernières offres."""
    import xml.etree.ElementTree as ET
    jobs, ok, ko = [], 0, 0
    for site in cfg.get("sites", []) or []:
        host = site.get("host", "").strip().strip("/")
        url = f"https://{host}/handlers/offerRss.ashx?LCID=1036"
        try:
            r = requests.get(url, headers=HEADERS, timeout=20)
            r.raise_for_status()
            root = ET.fromstring(r.content)
            ok += 1
        except (requests.RequestException, ET.ParseError) as e:
            print(f"[talentsoft] {site.get('name')} erreur : {e}")
            ko += 1
            continue
        for item in root.iter("item"):
            raw_title = (item.findtext("title") or "").strip()
            link = (item.findtext("link") or "").strip()
            # "2025-100324 - Stage - Analyste risques H/F" -> on retire la référence
            title = re.sub(r"^\d{4}-\d+\s*-\s*", "", raw_title)
            m = re.search(r"idOffre=(\d+)", link)
            jobs.append({
                "key": f"ts:{host}:{m.group(1) if m else link}",
                "source": site.get("name", host),
                "title": title,
                "company": site.get("name", host),
                "location": "",
                "posted": "",
                "posted_label": (item.findtext("pubDate") or "").strip(),
                "url": link,
                "is_internship_source": False,
            })
        polite_sleep()
    return jobs, ok, ko


# ---------------------------------------------------------------- filtrage
def keep(job: dict, conf: dict) -> bool:
    f = conf["filters"]
    title = job["title"]
    if not title:
        return False
    if not contains_any(title, f["include"]):
        return False
    if contains_any(title, f["exclude"]) or is_vie(title):
        return False
    if contains_any(title, f.get("seniority", [])):
        return False
    # L'intitulé doit dire que c'est un stage (le filtre "stage" de LinkedIn
    # laisse passer des CDI)
    if not contains_any(title, conf.get("internship_terms", [])):
        return False
    if not job["is_internship_source"]:
        loc = job.get("location", "")
        # Workday affiche parfois "3 Locations" : dans le doute on garde
        if loc and not re.search(r"\d+\s+locations?", loc, re.I):
            if not contains_any(loc, conf.get("allowed_locations", [])):
                return False
    return True


# ---------------------------------------------------------------- Telegram
def tg_send(text: str) -> None:
    token = os.environ.get("TELEGRAM_BOT_TOKEN")
    chat = os.environ.get("TELEGRAM_CHAT_ID")
    if not token or not chat:
        print("---- (pas de Telegram configuré, message affiché ici) ----")
        print(text)
        return
    r = requests.post(f"https://api.telegram.org/bot{token}/sendMessage",
                      data={"chat_id": chat, "text": text, "parse_mode": "HTML",
                            "disable_web_page_preview": "true"},
                      timeout=20)
    if not r.ok:
        print(f"[telegram] erreur {r.status_code} : {r.text}")
        r.raise_for_status()


def format_job(job: dict, priority_terms) -> str:
    e = html.escape
    fire = "🔥 " if contains_any(job["title"], priority_terms) else ""
    when = job.get("posted_label") or job.get("posted") or ""
    lines = [
        f"{fire}<b>{e(job['title'])}</b>",
        f"🏦 {e(job['company'])}",
        f"📍 {e(job['location'] or 'lieu non précisé')}" + (f"  ·  🕒 {e(when)}" if when else ""),
        f"🔗 {e(job['url'])}",
    ]
    return "\n".join(lines)


def send_jobs(jobs: list, priority_terms) -> None:
    # plus récentes d'abord, puis les 🔥 remontées en tête
    jobs = sorted(jobs, key=lambda j: j.get("posted", ""), reverse=True)
    jobs = sorted(jobs, key=lambda j: not contains_any(j["title"], priority_terms))
    header = f"🔔 <b>{len(jobs)} nouvelle(s) offre(s) de stage</b>"
    chunk = header
    for job in jobs:
        block = "\n\n" + format_job(job, priority_terms)
        if len(chunk) + len(block) > 3800:   # limite Telegram : 4096 caractères
            tg_send(chunk)
            chunk = "(suite)"
        chunk += block
    tg_send(chunk)


# ---------------------------------------------------------------- main
def main() -> int:
    conf = yaml.safe_load(CONFIG_FILE.read_text(encoding="utf-8"))
    state = load_state()
    # Si le dépôt a été copié par quelqu'un d'autre, on repart de zéro :
    # sa liste d'offres "déjà vues" ne doit pas être celle de l'auteur.
    repo = os.environ.get("GITHUB_REPOSITORY", "")
    if repo and state.get("repo") not in (None, repo):
        print(f"Nouveau dépôt ({repo}) : remise à zéro des offres vues")
        state = {"seen": {}, "consecutive_failures": 0, "last_heartbeat": ""}
    if repo:
        state["repo"] = repo
    first_run = not state["seen"]
    now = datetime.now(timezone.utc)

    if "--test" in sys.argv:
        tg_send("✅ Le bot de veille de stages est bien connecté à Telegram.")
        return 0

    all_jobs, total_ok, total_ko = [], 0, 0
    for fetch, key in [(fetch_linkedin, "linkedin"), (fetch_talentsoft, "talentsoft"),
                       (fetch_workday, "workday"), (fetch_smartrecruiters, "smartrecruiters")]:
        jobs, ok, ko = fetch(conf.get(key) or {})
        all_jobs += jobs
        total_ok += ok
        total_ko += ko
    print(f"Requêtes OK : {total_ok}, en erreur : {total_ko}, offres brutes : {len(all_jobs)}")

    # dédoublonnage (même offre trouvée par plusieurs mots-clés)
    unique = {}
    for j in all_jobs:
        unique.setdefault(j["key"], j)

    # même offre republiée sous un autre ID : on compare entreprise + intitulé
    seen_sigs = {v.get("sig") for v in state["seen"].values() if isinstance(v, dict)}
    new_jobs = []
    for j in unique.values():
        sig = norm(f"{j['company']}|{j['title']}")
        if j["key"] in state["seen"] or sig in seen_sigs:
            continue
        if keep(j, conf):
            new_jobs.append(j)
        # on mémorise aussi les offres rejetées pour ne pas les re-filtrer
        state["seen"][j["key"]] = {"t": now.isoformat(timespec="seconds"), "sig": sig}
        seen_sigs.add(sig)

    print(f"Nouvelles offres retenues : {len(new_jobs)}")
    for j in new_jobs:
        print(f"  + {j['company']} | {j['title']} | {j['location']}")

    prio = conf["filters"].get("priority", [])
    if first_run:
        sent = new_jobs[:FIRST_RUN_MAX_SENT]
        tg_send(f"🚀 Veille activée. {len(new_jobs)} offre(s) déjà en ligne correspondent "
                f"à tes critères" + (f", voici les {len(sent)} premières." if sent else "."))
        if sent:
            send_jobs(sent, prio)
    elif new_jobs:
        send_jobs(new_jobs, prio)

    # alerte si la veille est cassée (ex. LinkedIn bloque)
    if total_ok == 0:
        state["consecutive_failures"] = state.get("consecutive_failures", 0) + 1
        n = state["consecutive_failures"]
        if n % FAIL_ALERT_EVERY == 0:
            tg_send(f"⚠️ La veille échoue depuis {n} passages d'affilée (aucune source ne répond). "
                    "LinkedIn bloque peut-être temporairement. Regarde l'onglet Actions sur GitHub.")
    else:
        state["consecutive_failures"] = 0

    # purge des vieilles entrées
    cutoff = (now - timedelta(days=SEEN_RETENTION_DAYS)).isoformat()
    state["seen"] = {k: v for k, v in state["seen"].items()
                     if not isinstance(v, dict) or v.get("t", "") >= cutoff}

    # battement de cœur quotidien : garde le dépôt "actif" pour GitHub
    state["last_heartbeat"] = now.date().isoformat()
    save_state(state)
    return 0


if __name__ == "__main__":
    sys.exit(main())
