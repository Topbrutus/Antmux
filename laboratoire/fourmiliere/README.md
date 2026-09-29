# 🐜 Fourmilière publique — ANTMUX

## But

La Fourmilière publique est le journal de bord public ANTMUX et le point d'entrée pour les messages et propositions externes.

Le format visuel utilise EmojiLogic, mais la logique machine reste structurée et auditable.

## Signatures

```text
🐜📓 ... 📓🐜  = journal officiel
🐜✉️ ... ✉️🐜  = message
🐜💼 ... 💼🐜  = job / mandat / proposition
🐜📣 ... 📣🐜  = note publique
🧾             = reçu / trace
```

## Frontend

Page :

```text
/laboratoire/fourmiliere/
```

API utilisée par la page :

```text
/laboratoire/embryon-x72/api/journal/
```

Le frontend n'insère jamais le contenu visiteur avec `innerHTML`; le texte public est rendu avec `textContent`.

## API publique

```text
GET  /api/journal/config
GET  /api/journal/public
POST /api/journal/submit
```

Une soumission visiteur est toujours créée avec :

```text
status = PENDING
source = VISITOR
```

Elle n'apparaît donc jamais automatiquement dans le journal public.

## API de modération

```text
POST /api/journal/admin/publish
POST /api/journal/admin/moderate/{post_id}
```

Ces routes exigent :

```text
Authorization: Bearer <token>
```

Le token est généré localement sur le serveur dans :

```text
$ANTMUX_X72_DATA_DIR/journal-admin-token
```

Il ne doit jamais être commité ni exposé dans le frontend.

## Anti-spam V1

```text
3 soumissions maximum / fenêtre glissante de 24 h
120 secondes minimum entre deux soumissions
quota contrôlé par hash IP ET hash courriel
honeypot invisible
titre <= 160 caractères
message <= 3000 caractères
```

Les IP sont hashées avec un sel local persistant.
Les IP brutes ne sont pas stockées.

Le courriel du visiteur est conservé uniquement dans la base privée pour permettre une réponse.
Il n'est jamais retourné par l'API publique.

## Base de données

Fichier :

```text
$ANTMUX_X72_DATA_DIR/public-journal.db
```

Tables :

```text
posts
audit
```

Le journal conserve un audit séparé des changements de statut afin qu'une décision de modération laisse une trace.

## Courriel public ANTMUX

Le courriel affiché sur la page est lu dans cet ordre :

```text
ANTMUX_PUBLIC_CONTACT_EMAIL
$ANTMUX_X72_DATA_DIR/public-contact-email.txt
```

Le workflow de déploiement accepte le secret GitHub optionnel :

```text
ANTMUX_PUBLIC_CONTACT_EMAIL
```

S'il n'est pas configuré, la zone « courriel direct » reste simplement cachée.

## Test

```bash
ANTMUX_X72_DATA_DIR=/tmp/antmux-journal-test \
PYTHONPATH=deploy/x72-shared-queen \
python3 deploy/x72-shared-queen/tests/test_public_journal.py
```

Le test couvre :
- quota 3 / 24 h;
- délai minimum;
- modération;
- non-divulgation du courriel et des hashes;
- honeypot;
- porte admin;
- cadres EmojiLogic.

## Principe fourmi

```text
🐜 -> opcode / rôle -> action -> résultat -> 🧾 -> 📚
```

Pour une communication publique :

```text
🐜✉️ -> 📝 -> 👑 -> ✉️ -> 🧾 -> 📚
```

Pour une proposition de job :

```text
🐜💼 -> 📥 -> 🛡️ -> 📚 -> 👑 -> action
```

La Fourmilière ne donne jamais automatiquement aux workers une autorité supérieure à celle explicitement déléguée.
