# Politique de sécurité

## Signaler une faille

**N'ouvrez pas de ticket public pour une faille de sécurité.** Un ticket est
visible de tous, y compris de qui voudrait s'en servir avant le correctif.

Écrivez à **contact@bretagne-namaste.com**, avec en objet `[sécurité]`.
Si vous le pouvez, passez plutôt par l'avis de sécurité privé de GitHub :
onglet *Security* → *Report a vulnerability*.

Merci d'indiquer :

- ce que fait la faille, et ce qu'elle permet d'obtenir ;
- la version concernée (`phytoscope --version`, ou le contenu de
  `src/phytoscope/phytoscope/VERSION`) ;
- le système et la version de Python ;
- de quoi reproduire — la suite d'actions minimale, un fichier d'exemple ;
- si la faille est déjà connue ailleurs (CVE, avis amont).

### Ce à quoi vous pouvez vous attendre

| Étape | Délai visé |
|---|---|
| Accusé de réception | 5 jours ouvrés |
| Première évaluation (recevable ? gravité ?) | 15 jours |
| Correctif ou calendrier annoncé | 60 jours |
| Publication coordonnée de l'avis | après le correctif, avec votre accord |

Ce projet est porté par une petite structure : ces délais sont un engagement
d'effort, pas un contrat de service. Vous serez crédité dans l'avis et dans
le `CHANGELOG.md` si vous le souhaitez.

## Versions suivies

Seule la **dernière version publiée** reçoit des correctifs de sécurité. La
version en cours est dans `src/phytoscope/phytoscope/VERSION`.

## Portée

### Dans la portée

- le logiciel `src/phytoscope/` (Python, Qt) ;
- le micrologiciel `firmware/` (RP2350, C) ;
- la fabrique de paquets `packaging/` — en particulier la chaîne de
  **signature** (`packaging/signature.py`) et la vérification des paquets ;
- les outils `tools/` et les scripts de construction des ouvrages.

### Hors portée

- le fait qu'un **certificat auto-signé ne fait pas taire SmartScreen ni
  Gatekeeper**. Ce n'est pas une faille, c'est le fonctionnement attendu, et
  c'est écrit noir sur blanc dans `packaging/README.md` (contrainte `C-2Q`) ;
- les dépôts tiers recopiés sous `sources/` : signalez la faille **en amont**,
  chez le projet concerné, puis prévenez-nous pour que nous mettions à jour ;
- les documents et ouvrages (`pdf-src/`, `build/`) : une erreur de contenu n'est
  pas une faille — ouvrez un ticket ordinaire.

## Le secret qui compte dans ce dépôt : la clé privée de signature

La clé privée qui signe les paquets **n'est pas dans le dépôt et ne doit
jamais y entrer**.

- sa copie de référence vit dans `~/.local/share/phytoscope-signature/` ;
- `certificat/phytoscope.key` est une copie de travail, **écartée par
  `.gitignore`** (contrainte `C-2R`) ;
- le certificat X.509 **public** (`certificat/phytoscope-certificat.pem`,
  `certificat/phytoscope.crt`) est versionné : c'est lui qui permet de
  vérifier une signature, il est fait pour être diffusé.

`.gitignore` protège de `git`, **pas d'une sauvegarde ni d'une archive du
dossier**. Voir `certificat/LISEZ-MOI.md`.

Si vous pensez que la clé a fuité : écrivez à l'adresse ci-dessus en urgence.
La conduite à tenir est de révoquer, régénérer, et republier les paquets avec
de nouvelles empreintes.

### Vérifier qu'aucun secret n'est entré dans le dépôt

```bash
# Ce que git suit, qui ressemble à une clé
git ls-files | grep -Ei '\.(key|pem|p12|pfx|jks|keystore|asc|gpg)$'
# → seuls certificat/phytoscope-certificat.pem et certificat/phytoscope.crt
#   (publics) doivent apparaître.

# Le garde-fou local, posé par pre-commit
pre-commit run --all-files detection-cle-privee
```

## Vérifier l'authenticité d'un paquet

Chaque paquet publié est accompagné de son empreinte (`.sha256`) et de sa
signature CMS (`.p7s`). La marche à suivre est dans le fichier
`AUTHENTICITE.txt` livré avec les paquets, et la vérification complète se
relance par :

```bash
cd packaging && make verifier
```

## Ce que le projet fait pour sa propre sécurité

- **aucune dépendance obligatoire** ajoutée à la légère (contrainte `C-40`) ;
- **aucun `sudo`** : tout s'installe dans le dossier personnel (`C-55`) ;
- une **nomenclature logicielle** (SBOM, CycloneDX) versionnée dans
  `src/phytoscope/sbom.cdx.json`, régénérée par
  `.venv/bin/python tools/sbom.py --json` ;
- l'intégration continue passe `ruff`, `bandit`, `pip-audit`, `gitleaks` et
  la suite de tests à chaque poussée (voir `.github/workflows/`) ;
- les mises à jour de dépendances arrivent par Dependabot
  (`.github/dependabot.yml`).
