# 🔔 Ton bot de veille de stages, en 15 minutes

Ce bot surveille LinkedIn (et quelques sites carrières) toutes les 10 minutes. Il t'envoie sur **Telegram** chaque nouvelle offre de stage qui correspond à **tes** critères. Il est gratuit, tourne tout seul, et tu n'as pas besoin de savoir coder.

Il te faut juste un compte **GitHub** (gratuit) et **Telegram**.

---

## 1. Crée ton bot Telegram (3 min)

1. Dans Telegram, cherche **@BotFather** et envoie `/newbot`.
2. Choisis un nom, puis un identifiant qui finit par `bot` (ex. `veille_stage_lea_bot`).
3. BotFather te donne un **token** (`7123456789:AAH...`). Garde-le pour toi, ne le partage avec personne.
4. Clique sur le lien `t.me/...` dans son message, appuie sur **Démarrer**, puis envoie `salut` à ton bot.
5. Cherche **@userinfobot** dans Telegram et appuie sur **Démarrer**. Il te donne ton **Id** (un nombre). C'est ton **chat ID**.

## 2. Copie le bot sur ton GitHub (1 min)

1. Crée un compte sur github.com si tu n'en as pas.
2. Va sur la page du bot : **https://github.com/marouane2599-wq/stage**
3. Clique sur le bouton vert **Use this template**, puis sur **Create a new repository**.
4. Donne-lui un nom (ex. `veille-stage`), laisse-le en **Public** (les minutes sont alors illimitées et gratuites, et tes tokens restent cachés), puis clique sur **Create repository**.

## 3. Ajoute tes secrets (2 min)

Dans **ton** dépôt, va dans **Settings → Secrets and variables → Actions → New repository secret** et crée :

| Name | Valeur |
|---|---|
| `TELEGRAM_BOT_TOKEN` | le token de BotFather |
| `TELEGRAM_CHAT_ID` | ton Id de @userinfobot |

Ensuite, va dans **Settings → Actions → General → Workflow permissions**, coche **Read and write permissions** et clique sur **Save**.

## 4. Mets TES critères (5 min)

Ouvre le fichier `config.yaml` dans ton dépôt et clique sur le crayon ✏️ pour le modifier. Ce qu'il faut changer :

- `keywords` : ce que le bot tape dans la recherche LinkedIn.
- `locations` : les villes où tu cherches. Écris-les comme sur LinkedIn, par exemple `"Lyon, Auvergne-Rhône-Alpes, France"` ou `"Nice, Provence-Alpes-Côte d'Azur, France"`.
- `include` : l'intitulé doit contenir **au moins un** de ces mots.
- `exclude` : l'intitulé ne doit contenir **aucun** de ces mots.
- `priority` : ces mots ajoutent un 🔥 aux offres qui te correspondent le mieux.
- `talentsoft` (sites Amundi / CACEIS / Indosuez) : supprime les lignes qui ne t'intéressent pas.

Pas besoin d'accents ni de majuscules. Un mot trouve aussi ses variantes (`liquidit` trouve "liquidité"). Pour exiger le mot exact, ajoute un `!` à la fin (`market!` ne trouve pas "marketing").

Quand c'est fait, clique sur **Commit changes**.

### Exemples prêts à copier

**Audit / conseil**
```yaml
  keywords: [audit, "transaction services", conseil financier]
# include :
    - audit
    - auditeur
    - transaction services
    - conseil
    - consulting
    - commissariat aux comptes
    - controle interne
```

**Corporate finance / M&A**
```yaml
  keywords: ["M&A", "corporate finance", "fusions acquisitions", "private equity"]
# include :
    - m&a
    - merger
    - fusion
    - corporate finance
    - private equity
    - leveraged
    - ecm
    - dcm
    - investment banking
```

**Gestion de patrimoine / banque privée**
```yaml
  keywords: [patrimoine, "banque privée", "wealth management", "private banking"]
# include :
    - patrimoin
    - wealth
    - private bank
    - banque privee
    - family office
    - ingenierie patrimoniale
```

**Asset management**
```yaml
  keywords: ["asset management", "gestion d'actifs", "portfolio manager", "fund"]
# include :
    - asset management
    - gestion d'actifs
    - portfolio
    - gerant
    - fund
    - investment
    - multi-asset
```

⚠️ Garde au maximum 6 mots-clés × 3 villes. Au-delà, LinkedIn bloque le bot.

## 5. Lance-le

1. Va dans l'onglet **Actions** de ton dépôt. Si GitHub demande d'activer les workflows, accepte.
2. Clique sur **Veille stages → Run workflow**, coche **Envoyer juste un message test** et clique sur **Run**. Tu dois recevoir ✅ sur Telegram.
3. Relance **Run workflow** sans cocher la case. C'est le premier scan : tu reçois 🚀 et les offres déjà en ligne.
4. **C'est tout.** Ensuite, il tourne tout seul toutes les 10 minutes, de 6h à 23h.

---

### Ça ne marche pas ?
- **Croix rouge dans Actions** : clique dessus pour lire l'erreur. Le plus souvent, c'est un secret mal copié ou la permission "Read and write" oubliée.
- **Pas de message de test** : vérifie que tu as bien appuyé sur **Démarrer** dans la conversation avec **ton** bot.
- **Trop d'offres hors sujet** : ajoute les mots qui t'agacent dans `exclude`.
- **⚠️ "La veille échoue depuis 6 passages"** : LinkedIn bloque temporairement. Ça repart en général tout seul.

Le bot ne voit ni Jobteaser ni Indeed. Garde tes alertes classiques en parallèle.
