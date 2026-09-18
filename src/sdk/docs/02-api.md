# 2. L'interface, en détail

Tout ce qu'un module importe vient de `phytoscope.api`, et de nulle part
ailleurs. **Ce qui n'est pas dans ce fichier n'est pas de l'interface** : cela
peut changer d'une version à l'autre sans préavis.

```python
from phytoscope.api import (
    # le contrat
    VERSION_API, compatible, Manifeste, Module, Capacite,
    # les capacités
    Analyseur, Descripteur, Sonificateur, Exportateur, Source,
    # ce qu'elles échangent
    Grandeur, Trace, NoteProposee,
    # ce qu'on reçoit
    Contexte, EtatMesure,
    # les événements
    BUS, EVENEMENTS, MESURE_DEMARREE, EVENEMENT_DETECTE, ...,
)
```

---

## `VERSION_API` et la promesse de compatibilité

```python
VERSION_API = "1.0"
```

Numérotation sémantique :

| | |
|---|---|
| **majeur** | une promesse est rompue — un module ancien cesse de fonctionner |
| **mineur** | une capacité ou un paramètre s'ajoute, sans rien casser |
| **correctif** | une précision de comportement, jamais de forme |

```python
compatible("1.0")      # True  — même majeur, mineur suffisant
compatible("1.2")      # False sur une API 1.0 : elle ne connaît pas encore
compatible("2.0")      # False — majeur différent
```

**La promesse :** tant que le majeur ne change pas, un module écrit aujourd'hui
fonctionnera. On peut ajouter, on ne peut pas retirer.

Un module déclarant `api="1.0"` tourne sur toute API `1.x`. Il ne tourne pas
sur `2.x`, et le logiciel le lui dira plutôt que d'échouer au milieu d'une
séance.

---

## `Manifeste`

La carte d'identité. **Lue sans exécuter votre code** — voir
[les pièges](07-pieges.md#le-manifeste-est-lu-sans-executer-votre-code).

```python
Manifeste(
    nom="mon-module",
    titre="Mon module",
    version="1.0.0",
    api="1.0",
    description="",
    auteur="",
    licence="",
    site="",
    capacites=(),
    depend_de=(),
    exige=(),
)
```

### Les champs

| Champ | Type | Défaut | Rôle |
|---|---|---|---|
| `nom` | `str` | *obligatoire* | l'identifiant : `^[a-z][a-z0-9-]{1,48}$`. Sert de clé pour les réglages, le dossier, le journal. |
| `titre` | `str` | le nom | ce que l'utilisateur lit |
| `version` | `str` | `"0.1.0"` | la vôtre, en sémantique |
| `api` | `str` | la courante | la version d'interface visée |
| `description` | `str` | `""` | une phrase, affichée au Diagnostic |
| `auteur` | `str` | `""` | |
| `licence` | `str` | `""` | |
| `site` | `str` | `""` | |
| `capacites` | `tuple[str]` | `()` | **déclaratif** : ce qui n'est pas là n'est pas proposé, même si la méthode existe |
| `depend_de` | `tuple[str]` | `()` | les modules chargés avant le vôtre, par leur `nom` |
| `exige` | `tuple[str]` | `()` | les bibliothèques Python. Vérifiées **avant** l'import |

### Les méthodes

```python
manifeste.valide        # bool — le nom respecte-t-il la forme ?
manifeste.defauts()     # list[str] — ce qui empêche l'acceptation, en clair
manifeste.to_dict()     # dict
```

`defauts()` est ce que le Diagnostic affiche. Appelez-le dans vos essais :

```python
def test_le_manifeste_est_valide(instance):
    assert instance.MANIFESTE.defauts() == [], instance.MANIFESTE.defauts()
```

### `Capacite`

Des constantes, pour éviter les chaînes en dur :

```python
Capacite.ANALYSEUR      # "analyseur"
Capacite.DESCRIPTEUR    # "descripteur"
Capacite.SONIFICATEUR   # "sonificateur"
Capacite.EXPORTATEUR    # "exportateur"
Capacite.SOURCE         # "source"
Capacite.TOUTES         # le tuple des cinq
```

---

## `Module`

Ce dont hérite tout module. **Seul `MANIFESTE` est obligatoire** ; tout le
reste a un comportement par défaut qui ne fait rien.

```python
class Module:
    MANIFESTE: Manifeste

    def __init__(self, contexte: Contexte) -> None
    def installer(self) -> None
    def arreter(self) -> None
    def reglages_par_defaut(self) -> dict
```

### `__init__(contexte)`

Appelé au chargement. `self.contexte` est posé pour vous.

> **Ne faites rien de long ici.** C'est appelé pour tous les modules, l'un
> après l'autre, au démarrage du logiciel. Une seconde ici, c'est une seconde
> de plus avant que l'utilisateur ne voie quoi que ce soit.

### `installer()`

Une fois, **après** le chargement de tous les modules. C'est ici qu'on
s'abonne et qu'on prépare ses fichiers.

Pourquoi après tous les autres : si votre module dépend d'un autre
(`depend_de`), celui-ci est déjà chargé quand on vous appelle.

### `arreter()`

Une fois, à la fermeture. Fermez ce que vous avez ouvert. **Les abonnements
sont retirés pour vous** : inutile de s'en occuper.

### `reglages_par_defaut()`

```python
def reglages_par_defaut(self):
    return {"seuil_uv": 8.0, "montrer_le_detail": True}
```

Le logiciel les conserve sous le nom de votre module et vous les rend par
`contexte.reglages`. **N'écrivez jamais dans le fichier de réglages du
logiciel** : il ne vous appartient pas, et sa forme peut changer.

---

## `Contexte`

Ce que votre module reçoit. **Vous ne recevez jamais l'objet moteur** : c'est
délibéré, et c'est ce qui rend l'interface tenable dans le temps.

### Lire le signal

```python
contexte.signal(secondes=60.0, brut=False) -> np.ndarray
```

Les N dernières secondes, **en volts**, dans l'ordre chronologique. Rend un
tableau vide s'il n'y a rien encore — ce n'est pas une erreur, c'est le cas au
démarrage, et votre module doit le prévoir.

`brut=True` donne le signal **avant** réjecteur et passe-bas.

> **Quand employer le brut :** pour toute mesure de bruit. Filtrer avant de
> mesurer le bruit revient à mesurer son propre filtre — le réjecteur
> effacerait le résidu de secteur, le passe-bas à 40 Hz effacerait la bande où
> se lit le bruit thermique.
>
> **Quand employer le traité :** pour analyser l'*activité* de la plante
> plutôt que la chaîne de mesure.

### Les paramètres de la mesure

```python
contexte.frequence_hz       # float — la cadence réelle
contexte.pleine_echelle_v   # float — la pleine échelle du convertisseur
contexte.reseau_hz          # float — 50 ou 60, selon les réglages
```

### L'état

```python
etat = contexte.etat()      # EtatMesure — une copie, jamais une référence
```

| Champ | Type | |
|---|---|---|
| `en_marche` | `bool` | l'acquisition tourne |
| `source` | `str` | le nom de la source |
| `duree_s` | `float` | depuis le début de la séance |
| `frequence_hz` | `float` | |
| `tension_v` | `float` | la valeur instantanée |
| `ligne_de_base_v` | `float` | |
| `bruit_efficace_v` | `float` | |
| `crete_a_crete_v` | `float` | |
| `derive_v_par_min` | `float` | |
| `sature` | `bool` | le convertisseur bute |
| `evenements` | `int` | depuis le début |
| `notes` | `int` | |
| `enregistre` | `bool` | une séance est en cours d'écriture |
| `relecture` | `bool` | **on rejoue un enregistrement, on ne mesure pas** |

> `relecture` mérite l'attention : un module qui écrit quelque part doit
> savoir qu'il ne mesure pas.

```python
contexte.instants_evenements()   # list[float] — en secondes depuis le début
```

### Écrire

```python
contexte.dossier()    # str — votre répertoire, créé au besoin
```

`<configuration>/modules/<votre-nom>/`. Il survit aux mises à jour et n'est
jamais effacé par le logiciel.

> **Écrivez ici, et ici seul.** Rien ne vous en empêche techniquement — c'est
> du Python, pas une prison. Mais le dossier des séances appartient à
> l'utilisateur, et celui du logiciel au logiciel.

### Dire quelque chose

```python
contexte.journal("ce qui s'est passé", niveau="info")   # debug|info|warning|error
contexte.message("visible dans la barre d'état")
contexte.traduire("un libellé")
```

`journal()` écrit sous le nom de votre module : on retrouve vos lignes en
cherchant `module.<votre-nom>`.

`message()` **avec parcimonie** : un module qui parle sans cesse finit par ne
plus être lu.

### S'abonner

```python
contexte.abonner(EVENEMENT_DETECTE, self._sur_evenement)
```

Voir [4. Les événements](04-evenements.md).

---

## `Grandeur`

Ce que rend un analyseur.

```python
Grandeur(
    cle="mon-indicateur",       # identifiant, stable d'une version à l'autre
    libelle="Mon indicateur",   # un GABARIT si un nombre y figure
    valeur=3.14,                # le nombre, toujours fini
    texte="3,14 µV",            # la valeur mise en forme, unité comprise
    sens="Ce que ce nombre dit, et ce qu'il ne dit pas.",
    alerte=False,               # True → affiché en rouge
    params={},                  # les valeurs du gabarit
)
```

### `sens` n'est pas décoratif

Le logiciel impose que toute valeur affichée dise ce qu'elle signifie **et ce
qu'elle ne permet pas de conclure**. Un module qui ne l'explique pas est
chargé quand même, mais l'interface écrit *« le module n'explique pas cette
valeur »* — ce qui se remarque.

### `libelle` et `params` : les gabarits

Un libellé qui contient un nombre doit être un **gabarit** :

```python
#  NON — cette phrase ne peut pas entrer dans un catalogue de traduction
Grandeur(libelle=f"Écart d'Allan à {tau} s", ...)

#  OUI
Grandeur(libelle="Écart d'Allan à {tau} s", params={"tau": f"{tau:g}"}, ...)
```

L'interface traduit **puis** remplit les trous. Une phrase où le nombre est
déjà incrusté est intraduisible.

### `texte` : des symboles, pas des mots

```python
texte="+37.2 dB"                        # OUI
texte="+37.2 dB au-dessus du plancher"  # NON — reste en français partout
```

Les symboles d'unité sont internationaux ; les mots vont dans `libelle` ou
`sens`, qui sont traduits.

---

## `Trace`

Ce que rend un descripteur.

```python
Trace(
    x=np.ndarray, y=np.ndarray,   # même taille, sinon ValueError
    titre="",
    x_libelle="", y_libelle="",
    x_log=False, y_log=False,
    avertissement="",             # affiché sous la courbe
)
```

`avertissement` joue le rôle de `sens` : ce que la représentation suppose, et
ce qu'elle ne permet pas de conclure.

---

## `NoteProposee`

Ce que rend un sonificateur. **L'hôte décide de la jouer.**

```python
NoteProposee(
    hauteur_midi=60,    # 0–127
    velocite=80,        # 0–127
    duree_s=0.4,
    canal=0,
    origine_v=0.0,      # la valeur mesurée qui a produit cette note
)
```

`origine_v` est conservée dans le rendu. Une sonification dont on ne peut plus
remonter à la mesure n'est plus une mesure.

---

**Suite :** [3. Les cinq capacités](03-capacites.md)
