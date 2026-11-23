# Mon bot de veille de stages

Salut ! Si t'es là, c'est que je t'ai envoyé le lien 😄

Le principe : j'en avais marre de voir les offres 3 jours après tout le monde. Du coup, j'ai monté un bot qui fouille LinkedIn toutes les 10 minutes (plus les sites carrières d'Amundi, CACEIS et Indosuez). Dès qu'une offre de stage qui me correspond sort, je la reçois direct sur Telegram, avec le lien. Moi je l'ai réglé sur le risque et le middle office, mais toi tu le règles sur ce que tu veux.

C'est gratuit, ça tourne tout seul une fois lancé, et t'as pas besoin de savoir coder. Il te faut juste un compte GitHub et Telegram. Compte 15-20 min la première fois. Je te préviens, l'étape GitHub peut paraître chelou si t'as jamais utilisé, mais suis juste les étapes dans l'ordre et ça passe.

---

### Étape 1 : ton bot Telegram

Sur Telegram, cherche **@BotFather** et envoie-lui `/newbot`. Il te demande un nom (mets ce que tu veux), puis un identifiant qui finit par `bot`, genre `veille_stage_lea_bot`.

Il te renvoie un **token**, un truc du style `7123456789:AAH...`. Copie-le quelque part et **ne le donne à personne**, c'est la clé de ton bot.

Ensuite, clique sur le lien `t.me/...` dans son message pour ouvrir ton bot, appuie sur **Démarrer** et envoie-lui n'importe quoi (genre "salut"). Si tu fais pas ça, il pourra pas t'écrire.

Dernier truc : cherche **@userinfobot**, appuie sur **Démarrer**, il te donne ton **Id** (un nombre). Garde-le aussi.

### Étape 2 : copier le bot sur ton GitHub

Crée-toi un compte sur github.com si t'en as pas. Ensuite, va sur ma page : **https://github.com/marouane2599-wq/stage**

Clique sur le bouton vert **Use this template**, puis sur **Create a new repository**. Donne-lui un nom (`veille-stage` par exemple), laisse-le en **Public** et valide. En public c'est gratuit et illimité, et t'inquiète, tes codes Telegram restent cachés.

### Étape 3 : brancher ton Telegram

Dans **ton** dépôt (pas le mien), va dans **Settings**, puis **Secrets and variables**, puis **Actions**, et clique sur **New repository secret**. Tu en crées deux :
- un qui s'appelle `TELEGRAM_BOT_TOKEN`, avec le token de BotFather dedans
- un qui s'appelle `TELEGRAM_CHAT_ID`, avec ton Id de @userinfobot

Toujours dans Settings, va dans **Actions**, puis **General**, descends tout en bas jusqu'à **Workflow permissions**, coche **Read and write permissions** et clique sur **Save**. Si tu oublies ça, le bot plante.

### Étape 4 : mettre tes critères

C'est là que tu le règles pour toi. Ouvre le fichier `config.yaml` dans ton dépôt et clique sur le petit crayon pour le modifier.

Les trucs à changer :
- **keywords** : ce que le bot tape dans la recherche LinkedIn
- **locations** : tes villes, écrites comme sur LinkedIn (`"Lyon, Auvergne-Rhône-Alpes, France"`, `"Nice, Provence-Alpes-Côte d'Azur, France"`…)
- **include** : l'intitulé de l'offre doit contenir au moins un de ces mots
- **exclude** : si l'intitulé contient un de ces mots, poubelle (alternance, CDI, etc.)
- **priority** : les mots qui te tiennent le plus à cœur. Les offres qui les contiennent arrivent avec un 🔥
- **talentsoft** : les sites Amundi, CACEIS et Indosuez. Vire ceux qui t'intéressent pas

Pas besoin d'accents ni de majuscules. Et un mot attrape ses variantes : `liquidit` trouve "liquidité". Si tu veux le mot exact, mets un `!` à la fin : `market!` évite de te ramener du "marketing".

Fais gaffe à pas mettre trop de mots-clés et de villes : max 6 mots-clés × 3 villes, sinon LinkedIn bloque.

Quand t'as fini, clique sur **Commit changes**.

Je t'ai mis des exemples selon ce que tu cherches, t'as juste à remplacer les lignes :

**Audit / conseil**
```yaml
  keywords: [audit, "transaction services", conseil financier]
# dans include :
    - audit
    - auditeur
    - transaction services
    - conseil
    - consulting
    - controle interne
```

**Corporate finance / M&A**
```yaml
  keywords: ["M&A", "corporate finance", "fusions acquisitions", "private equity"]
# dans include :
    - m&a
    - merger
    - fusion
    - corporate finance
    - private equity
    - investment banking
```

**Patrimoine / banque privée**
```yaml
  keywords: [patrimoine, "banque privée", "wealth management", "private banking"]
# dans include :
    - patrimoin
    - wealth
    - private bank
    - banque privee
    - ingenierie patrimoniale
```

**Asset management**
```yaml
  keywords: ["asset management", "gestion d'actifs", "portfolio manager"]
# dans include :
    - asset management
    - gestion d'actifs
    - portfolio
    - gerant
    - fund
```

### Étape 5 : le lancer

Va dans l'onglet **Actions** de ton dépôt. Si GitHub te demande d'activer les workflows, dis oui.

Clique sur **Veille stages** à gauche, puis sur **Run workflow** à droite. Coche la case **Envoyer juste un message test** et lance. Tu dois recevoir un ✅ sur Telegram. Si c'est bon, relance **Run workflow** sans cocher la case : là il fait son premier vrai scan et t'envoie les offres déjà en ligne.

Après ça, t'as plus rien à faire. Il tourne tout seul toutes les 10 min, de 6h à 23h, et il t'écrit seulement quand il y a du nouveau.

---

### Si ça marche pas

- **Croix rouge dans Actions** : clique dessus pour voir l'erreur. 9 fois sur 10, c'est un secret mal copié ou t'as oublié le "Read and write" de l'étape 3.
- **Rien sur Telegram** : vérifie que t'as bien appuyé sur Démarrer dans la conv avec **ton** bot.
- **Il t'envoie des offres nulles** : ajoute les mots qui te saoulent dans `exclude`.
- **Message "la veille échoue"** : LinkedIn bloque de temps en temps, en général ça repart tout seul.

Et garde quand même tes alertes Jobteaser et LinkedIn à côté, le bot voit pas tout.

Si tu bloques, écris-moi. Bonne chance pour les candidatures 🤞

Marouane
