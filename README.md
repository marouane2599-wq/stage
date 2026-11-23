# Bot de veille de stages (GitHub + Telegram)

Toutes les 10 minutes, de 6h à 23h, le bot interroge LinkedIn et les sites carrières d'Amundi, CACEIS et Indosuez (plus ceux que tu ajoutes). Il filtre les offres selon `config.yaml` et t'envoie chaque **nouvelle** offre sur Telegram. 🔥 = ton cœur de cible (risque de marché, contrepartie, ALM, liquidité…).

Ça te prend environ 15 minutes à installer, et c'est gratuit.

---

## Étape 1 : créer ton bot Telegram (3 min)

1. Dans Telegram, cherche **@BotFather** et envoie `/newbot`.
2. Donne-lui un nom (ex. `Veille Stage Marouane`), puis un identifiant qui finit par `bot` (ex. `veille_stage_mm_bot`).
3. BotFather te renvoie un **token** du genre `7123456789:AAH...`. Copie-le et ne le partage avec personne.
4. Ouvre la conversation avec ton nouveau bot et envoie-lui `salut` (obligatoire, sinon il ne peut pas t'écrire).
5. Dans ton navigateur, ouvre cette adresse en remplaçant `TON_TOKEN` :
   `https://api.telegram.org/botTON_TOKEN/getUpdates`
   Cherche `"chat":{"id":` suivi d'un nombre (ex. `512345678`). C'est ton **chat ID**.

## Étape 2 : créer le dépôt GitHub (5 min)

1. Crée un compte sur github.com si tu n'en as pas.
2. Clique sur **New repository**, nomme-le `veille-stage` et choisis **Public**.
   *Pourquoi public ?* Les minutes sont illimitées. En privé, tu es plafonné à 2000 min/mois et un passage toutes les 10 min dépasse ce plafond. Tes tokens restent secrets dans les deux cas : on ne voit que tes mots-clés.
3. Clique sur **uploading an existing file** et glisse **tout le contenu** du dossier dézippé : `bot.py`, `config.yaml`, `requirements.txt`, `README.md` et le dossier `.github`.
   ⚠️ Sur Mac, le dossier `.github` est caché. Dans le Finder, fais **Cmd + Maj + .** pour l'afficher.
   S'il ne passe pas, crée-le à la main : **Add file → Create new file**, tape le nom `.github/workflows/veille.yml` et colle le contenu du fichier.
4. Clique sur **Commit changes**.

## Étape 3 : ajouter tes secrets (2 min)

Va dans **Settings → Secrets and variables → Actions → New repository secret** et crée-en deux :

| Name | Valeur |
|---|---|
| `TELEGRAM_BOT_TOKEN` | le token de BotFather |
| `TELEGRAM_CHAT_ID` | ton chat ID |

Puis va dans **Settings → Actions → General → Workflow permissions**, coche **Read and write permissions** et clique sur **Save**.

## Étape 4 : tester

1. Ouvre l'onglet **Actions**. Si GitHub demande d'activer les workflows, clique pour accepter.
2. Clique sur **Veille stages → Run workflow**, coche **Envoyer juste un message test** et clique sur **Run**.
   ✅ Tu dois recevoir « Le bot de veille de stages est bien connecté » sur Telegram.
3. Relance **Run workflow**, cette fois sans cocher la case. C'est le premier scan : tu reçois « 🚀 Veille activée » et les offres déjà en ligne (15 max).
4. Ensuite, ça tourne tout seul.

---

## Modifier tes critères

Sur GitHub, ouvre `config.yaml`, clique sur le crayon ✏️, modifie, puis **Commit**. C'est pris en compte au passage suivant.
- Ajouter une recherche LinkedIn : ajoute un mot dans `keywords` ou un lieu dans `locations`. Évite de dépasser une vingtaine de combinaisons mot-clé × lieu, sinon LinkedIn te bloque.
- Une offre passe alors qu'elle ne devrait pas : ajoute un mot de son intitulé dans `exclude`.
- Ajouter le site carrières d'une banque qui utilise **Workday** (URL en `...myworkdayjobs.com/...`) : colle l'URL dans `workday → sites`.

## Changer la fréquence

Dans `.github/workflows/veille.yml`, modifie la ligne `cron`. Les horaires sont en **UTC** (Paris = UTC+1 en hiver, UTC+2 en été).
- `*/10 5-22 * * *` : toutes les 10 min de 6h à 23h (réglage actuel)
- `*/5 5-22 * * *` : toutes les 5 min (le minimum de GitHub)
- Si ton dépôt est privé, passe à `*/20 6-21 * * *` pour rester sous les 2000 min gratuites.

## Limites à connaître

- **GitHub ne garantit pas l'heure exacte** : aux heures de pointe, un passage peut avoir 5 à 20 minutes de retard. Ça reste bien plus rapide qu'une alerte e-mail quotidienne.
- **LinkedIn peut bloquer temporairement** les serveurs de GitHub. Si plus rien ne passe pendant 6 passages d'affilée, le bot t'envoie un ⚠️ sur Telegram. En général, ça repart tout seul.
- **Garde quand même tes alertes LinkedIn / Jobteaser / sites carrières** en parallèle : le bot ne voit pas Jobteaser (connexion requise), ni les banques qui n'utilisent ni LinkedIn ni Workday.
