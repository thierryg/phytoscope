# 7. Les pièges

Ce qui coûte une soirée quand on l'ignore. Ils sont tous réels : chacun a été
rencontré en écrivant les modules livrés avec le logiciel.

---

## Le manifeste est lu sans exécuter votre code

Le logiciel analyse syntaxiquement `module.py` pour en extraire le manifeste,
**avant** de l'importer.

```python
#  NON — ne sera pas lu, le défaut « 0.1.0 » s'appliquera
MANIFESTE = Manifeste(nom="mon-module", version=lire_ma_version())

#  NON — pareil
VERSION = "1.0.0"
MANIFESTE = Manifeste(nom="mon-module", version=VERSION)

#  OUI
MANIFESTE = Manifeste(nom="mon-module", version="1.0.0")
```

Seules les constantes de `Capacite` font exception, parce qu'elles
appartiennent au contrat :

```python
capacites=(Capacite.ANALYSEUR,)          # lu correctement
capacites=("analyseur",)                 # lu aussi, mais moins lisible
capacites=mes_capacites()                # PAS lu
```

**Pourquoi c'est ainsi :** pour lister les modules présents, en désactiver un
et refuser celui qui vise une interface inconnue, il faut connaître le
manifeste. L'obtenir en exécutant le module reviendrait à lui faire confiance
avant de savoir s'il le mérite.

---

## Ne jamais lever pour dire « rien à signaler »

```python
#  NON — désactive votre module pour toute la séance
def analyser(self, x, fs, contexte):
    if x.size == 0:
        raise ValueError("pas de signal")

#  OUI
def analyser(self, x, fs, contexte):
    if x.size == 0:
        return []
```

Une exception, où qu'elle survienne, **désactive votre module jusqu'au
prochain démarrage**. C'est délibéré : un module qui échoue une fois échouera
sans doute encore, et laisser filer produirait la même trace toutes les deux
secondes.

---

## Ne rien faire de long dans `__init__`

```python
#  NON — retarde le démarrage de TOUS les modules
def __init__(self, contexte):
    super().__init__(contexte)
    self._table = charger_dix_megaoctets()

#  OUI
def installer(self):
    self._table = charger_dix_megaoctets()

#  MIEUX — à la première utilisation
def analyser(self, x, fs, contexte):
    if self._table is None:
        self._table = charger_dix_megaoctets()
```

---

## Les libellés avec un nombre doivent être des gabarits

```python
#  NON — cette phrase ne peut entrer dans aucun catalogue de traduction
Grandeur(libelle=f"Écart d'Allan à {tau} s", ...)

#  OUI
Grandeur(libelle="Écart d'Allan à {tau} s",
         params={"tau": f"{tau:g}"}, ...)
```

L'interface **traduit d'abord, remplit ensuite**. Un libellé où le nombre est
déjà incrusté est intraduisible : il restera en français dans les dix autres
langues.

---

## `texte` ne contient que des symboles d'unité

```python
texte="+37.2 dB"                        # OUI — les symboles sont internationaux
texte="+37.2 dB au-dessus du plancher"  # NON — « au-dessus du plancher »
                                        #       restera en français partout
```

Les mots vont dans `libelle` ou dans `sens`, qui sont traduits. Ce piège est
d'autant plus facile qu'il ne se voit pas depuis une interface française.

---

## Filtrer avant de mesurer le bruit

```python
SIGNAL_BRUT = False     # NON, si vous mesurez du bruit
```

Le signal traité a traversé le réjecteur de réseau et le passe-bas à 40 Hz.
Mesurer le bruit dessus revient à **mesurer son propre filtre** : le résidu de
secteur a été retiré, et la bande où se lit le bruit thermique aussi.

```python
SIGNAL_BRUT = True      # pour toute mesure de bruit
```

---

## Écrire ailleurs que chez soi

```python
#  NON — le dossier de la séance appartient à l'utilisateur
chemin = os.path.join(seance, "mon-fichier.txt")

#  OUI
chemin = os.path.join(self.contexte.dossier(), "mon-fichier.txt")
```

Rien ne vous en empêche techniquement. Mais un module qui salit le dossier des
séances sera désinstallé, et à juste titre.

---

## Les rappels d'événements doivent être courts

```python
#  NON — vous êtes dans le fil de l'interface
def _sur_evenement(self, instant_s, amplitude_v):
    self._recalculer_tout_le_spectre()

#  OUI — on note, on calcule ailleurs
def _sur_evenement(self, instant_s, amplitude_v):
    self._a_traiter.append((instant_s, amplitude_v))
```

Trente millisecondes à chaque événement, sur une plante active, se voient à
l'écran.

---

## Un rappel qui lève est désabonné, définitivement

Si votre module « cesse de réagir » après quelques minutes, regardez le
journal : vous y trouverez la faute et l'heure à laquelle il a été débranché.

Ce n'est pas une punition : laisser branché un abonné fautif noierait le
journal sous la même trace — celui-là même dont on a besoin pour comprendre.

---

## N'importer que depuis `phytoscope.api`

```python
#  NON — cassera sans préavis, et nous ne le saurons pas
from phytoscope.core.engine import Engine
from phytoscope.core.analysis import spectre

#  OUI
from phytoscope.api import Analyseur, Grandeur, Manifeste, Module
```

Le moteur change à chaque version. `phytoscope.api` ne change pas tant que le
majeur ne change pas — c'est toute la différence, et c'est écrit dans le
contrat.

Si quelque chose vous manque dans l'interface, **dites-le** : c'est
précisément ainsi qu'elle s'enrichira.

---

## Deux fichiers d'essais de même nom

```
mon-module/test_module.py
autre-module/test_module.py     ← pytest refuse de collecter les deux
```

Nommez-les `test_<votre-module>.py`. L'outil `nouveau_module.py` le fait.

---

## Oublier `sens`

```python
#  Chargé quand même — mais l'interface écrira, à votre place :
#  « le module « mon-module » n'explique pas cette valeur »
Grandeur(cle="x", libelle="X", valeur=1.0, texte="1")
```

Un nombre sans son interprétation est une invitation à se tromper. « 618 kΩ »
ne signifie rien si l'on ignore que c'est un majorant déduit du bruit, et non
une résistance mesurée à l'ohmmètre.

---

## Résumé

| Le piège | Le symptôme | La règle |
|---|---|---|
| manifeste calculé | les défauts s'appliquent | des littéraux |
| exception pour « rien » | module désactivé | rendre `[]` |
| `__init__` long | démarrage lent | `installer()` |
| libellé non gabarit | intraduisible | `{param}` + `params` |
| mots dans `texte` | français partout | symboles seulement |
| signal traité pour le bruit | on mesure son filtre | `SIGNAL_BRUT = True` |
| écrire ailleurs | module désinstallé | `contexte.dossier()` |
| rappel long | affichage saccadé | noter, calculer ailleurs |
| import hors API | casse à la mise à jour | `phytoscope.api` |
| `sens` absent | l'interface vous dénonce | toujours l'écrire |

---

**Retour :** [README du SDK](../README.md)
