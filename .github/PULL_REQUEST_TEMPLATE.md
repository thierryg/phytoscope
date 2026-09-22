## Ce que fait cette demande

<!-- En une ou deux phrases, et surtout : pourquoi. -->

## Pourquoi

<!--
La règle du dépôt : un commentaire qui paraphrase le code est à supprimer,
un commentaire qui dit pourquoi le code est ainsi est à garder. Même chose
ici. S'il y a un ticket, renvoyez-y : « corrige #12 ».
-->

## Ce que j'ai vérifié

<!-- Cochez ce que vous avez réellement lancé. Les cases non cochées ne sont
     pas un reproche : elles disent au relecteur où regarder. -->

- [ ] `cd src/phytoscope && make test` — la suite passe
- [ ] `cd src/phytoscope && make lint`
- [ ] `pre-commit run --all-files`
- [ ] `python3 tools/headers.py --verifier` — les en-têtes sont à jour
- [ ] `python3 tools/verify_svg.py` — si j'ai touché aux illustrations
- [ ] Les publications se reconstruisent — si j'ai touché à `pdf-src/` ou aux `build_*.py`
- [ ] `cd packaging && make tout && make verifier` — si j'ai touché à l'empaquetage

## Chiffres

<!--
Le dépôt impose de mesurer avant d'affirmer. Si votre texte annonce un
nombre — de pages, de tests, de références, un prix, un débit — donnez la
commande qui le produit.
-->

## Ce que j'ai consigné

- [ ] Entrée datée dans `.ai/journal.md`
- [ ] `.ai/etat.md` mis à jour
- [ ] `.ai/decisions.md` — si ceci tranche une question de conception
- [ ] `CHANGELOG.md` — si cela se voit de l'extérieur
- [ ] `constraints.md` — si une contrainte change (et alors, dites laquelle)

## Contrôles du dépôt

- [ ] Tout est en français, typographie comprise
- [ ] Aucune dépendance obligatoire ajoutée (`C-40`)
- [ ] Aucun `sudo` (`C-55`)
- [ ] Aucun fichier généré modifié à la main (`C-45`)
- [ ] **Aucune clé privée, aucun secret** (`C-2R`)
- [ ] Aucun en-tête d'attribution posé sur du code tiers (`sources/`)
