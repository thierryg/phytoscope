# Licences — deux, et c'est voulu

Le dépôt porte **deux licences**, parce qu'il porte deux natures d'objets
(contrainte `C-53` du cahier des charges).

| Ce qui est couvert | Licence | Identifiant SPDX | Texte |
|---|---|---|---|
| Logiciel (`src/phytoscope/`), micrologiciel (`src/firmware/`), trousse (`src/sdk/`), outils (`tools/`, `packaging/`), scripts de construction | **MIT** | `MIT` | [`MIT.txt`](MIT.txt) — et [`../LICENSE`](../LICENSE) à la racine |
| Matériel : cartes, schémas, nomenclatures (`hardware/`) | **CERN-OHL-P v2** | `CERN-OHL-P-2.0` | [`CERN-OHL-P-2.0.txt`](CERN-OHL-P-2.0.txt) |

Écrire « MIT » sur un plan de circuit serait faux, et un jour quelqu'un s'en
servirait en le croyant. D'où la seconde licence, et d'où le fait que
`tools/headers.py` la pose automatiquement sur tout fichier vivant sous
`hardware/`.

## Comment savoir quelle licence s'applique à un fichier

Chaque fichier source porte son identifiant SPDX dans son en-tête
d'attribution :

```
SPDX-License-Identifier: MIT
```

Pour le vérifier sur l'ensemble du dépôt :

```bash
python3 tools/headers.py --verifier
```

## Ce qui n'est ni l'un ni l'autre

Le dépôt s'appuie sur des travaux tiers qui gardent **leur propre licence** :

- `sources/schematics/` — schémas et bibliothèques tiers, recopiés **avec** leur
  fichier de licence (LEDFader, biotron-firmware, midisprout) ;
- `sources/software/MANIFESTE.md` — la liste des dépôts tiers utilisés, avec
  leur licence et leur provenance. Les archives elles-mêmes ne sont pas
  versionnées : `python3 tools/fetch-software.py` les récupère à la source ;
- `pdf-src/assets/fonts/` — Cinzel et Cormorant Garamond, sous SIL Open Font
  License 1.1 ;
- `pdf-src/assets/img/photos/CREDITS.md` — l'origine et la licence de chaque
  photographie et de chaque planche.

Les documents sous droits utilisés pour la documentation (ouvrages, articles
payants, notices constructeurs) **ne sont pas dans le dépôt** : ils sont
écartés par `.gitignore`. Voir [`../SECURITY.md`](../SECURITY.md) pour le
raisonnement, et `sources/INDEX.md` pour leurs références bibliographiques.
