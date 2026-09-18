# 6. Publier son module

Trois façons de diffuser, de la plus simple à la plus formelle.

---

## 1. Un dossier

La plus simple, et souvent suffisante. Compressez le dossier, publiez-le.

```bash
tar czf mon-module-1.0.0.tar.gz mon-module/
```

L'utilisateur le décompresse dans son dossier de modules :

| Système | Dossier |
|---|---|
| Linux | `~/.config/phytoscope/modules/` |
| macOS | `~/Library/Application Support/PhytoScope/modules/` |
| Windows | `%APPDATA%\PhytoScope\modules\` |

**Joignez l'empreinte** — c'est du code qui s'exécutera chez quelqu'un :

```bash
sha256sum mon-module-1.0.0.tar.gz > mon-module-1.0.0.tar.gz.sha256
```

---

## 2. Un dépôt Git

```
mon-module/
    module.py
    test_mon_module.py
    README.md
    LICENCE.txt
    CHANGELOG.md
```

L'utilisateur clone directement dans son dossier de modules :

```bash
git clone https://… ~/.config/phytoscope/modules/mon-module
```

Ce qu'un `README.md` de module doit dire, dans cet ordre :

1. **ce que fait le module, en une phrase** ;
2. **ce qu'il ne fait pas** — la question que tout le monde se posera ;
3. comment l'installer ;
4. les réglages, avec leurs valeurs par défaut ;
5. la version d'interface visée et les versions de PhytoScope compatibles ;
6. la licence.

---

## 3. Un paquet Python

Pour diffuser sur PyPI. Déclarez un point d'entrée :

```toml
# pyproject.toml
[project]
name = "phytoscope-mon-module"
version = "1.0.0"
dependencies = ["numpy>=1.24"]

[project.entry-points."phytoscope.modules"]
mon-module = "phytoscope_mon_module:MonModule"
```

```bash
pip install phytoscope-mon-module
```

Le logiciel découvre les points d'entrée au démarrage, en plus des dossiers.

> **Le nom du paquet** gagne à commencer par `phytoscope-` : cela le rend
> trouvable, et dit tout de suite à quoi il sert.

---

## Versionner

### Votre version

Numérotation sémantique, comme partout :

| | |
|---|---|
| **majeur** | un réglage disparaît, un comportement change |
| **mineur** | une grandeur s'ajoute, un réglage apparaît |
| **correctif** | une correction, sans changement visible |

### La version d'interface visée

```python
api="1.0"
```

**Visez le plus bas qui suffise.** Un module qui déclare `api="1.0"` tourne
sur toutes les versions `1.x` ; un module qui déclare `api="1.3"` refuse de
tourner sur une 1.2, même s'il n'emploie rien de nouveau.

Ne montez ce numéro que le jour où vous employez réellement quelque chose
ajouté dans cette version-là.

---

## Le contrat de compatibilité

Ce que nous promettons, tant que le majeur de `VERSION_API` ne change pas :

* les classes, les méthodes et les champs existants **restent** ;
* leur comportement **ne change pas** ;
* nous pouvons **ajouter** des capacités, des champs, des événements.

Ce que nous ne promettons pas :

* que ce qui n'est pas dans `phytoscope.api` reste. Si votre module importe
  `phytoscope.core.quelque_chose`, il cassera, et nous ne le saurons même pas.

Le jour où il faudra rompre — cela arrivera — le majeur changera, le logiciel
refusera de charger les modules anciens **en le disant clairement**, et la
documentation expliquera la migration.

---

## Une liste de vérification avant de publier

- [ ] `MANIFESTE.defauts()` rend une liste vide
- [ ] les essais passent : `python3 -m pytest mon-module/ -v`
- [ ] le module traverse les cas limites sans lever : signal vide, nul, saturé
- [ ] chaque `Grandeur` a un `sens` qui dit ce qu'elle ne permet pas de conclure
- [ ] les libellés contenant un nombre sont des **gabarits** avec `params`
- [ ] `texte` ne contient que des symboles d'unité, pas de mots
- [ ] le module n'écrit que dans `contexte.dossier()`
- [ ] les rappels d'événements sont courts
- [ ] `auteur` et `licence` sont renseignés dans le manifeste
- [ ] le `README` dit ce que le module **ne fait pas**
- [ ] l'empreinte SHA-256 accompagne l'archive

---

**Suite :** [7. Les pièges](07-pieges.md)
