# 4. Les événements

Un module n'interroge pas le logiciel en boucle : il dit ce qui l'intéresse,
et l'hôte l'appelle. C'est le seul moyen d'avoir des modules qui ne coûtent
rien quand il ne se passe rien.

```python
from phytoscope.api import EVENEMENT_DETECTE

def installer(self):
    self._compte = 0
    self.contexte.abonner(EVENEMENT_DETECTE, self._sur_evenement)

def _sur_evenement(self, instant_s, amplitude_v):
    self._compte += 1
```

---

## La liste complète

| Constante | Chaîne | Le rappel reçoit |
|---|---|---|
| `MESURE_DEMARREE` | `mesure.demarree` | `(etat: EtatMesure)` |
| `MESURE_ARRETEE` | `mesure.arretee` | `(etat: EtatMesure)` |
| `SOURCE_CHANGEE` | `mesure.source` | `(nom: str)` |
| `EVENEMENT_DETECTE` | `signal.evenement` | `(instant_s: float, amplitude_v: float)` |
| `NOTE_JOUEE` | `musique.note` | `(hauteur_midi: int, velocite: int)` |
| `ENONCE_PRODUIT` | `parole.enonce` | `(texte: str)` |
| `SEANCE_COMMENCEE` | `seance.commencee` | `(dossier: str)` |
| `SEANCE_TERMINEE` | `seance.terminee` | `(dossier: str)` |
| `ECHANTILLON_CAPTURE` | `echantillon.capture` | `(chemin: str)` |
| `REGLAGES_MODIFIES` | `reglages.modifies` | *(rien)* |
| `ALERTE_DISQUE` | `disque.alerte` | `(megaoctets_restants: float)` |

`EVENEMENTS` est un dictionnaire de ces chaînes vers leur description :

```python
from phytoscope.api import EVENEMENTS
for nom, description in EVENEMENTS.items():
    print(f"{nom:<24} {description}")
```

---

## Ce que l'hôte garantit

### Les rappels viennent du fil de l'interface

**Jamais du fil d'acquisition.** Un module qui met trente millisecondes à
répondre ralentit l'affichage ; il ne fait pas tomber un échantillon.

Ce n'est pas une permission d'être lent. Trente millisecondes à chaque
événement, sur une plante active, se voient.

### Un rappel qui lève est désabonné

Immédiatement, et l'incident est inscrit au journal avec le nom de votre
module.

C'est délibéré. Laisser branché un abonné fautif reviendrait à inscrire la
même trace toutes les secondes, et à rendre le journal illisible — celui-là
même dont on a besoin pour comprendre la panne.

> **Conséquence :** si votre module « cesse de réagir » après un moment,
> regardez le journal. Vous y trouverez la faute, et l'heure à laquelle il a
> été débranché.

### L'ordre d'appel est celui de l'abonnement

Déterministe, donc reproductible.

### Le désabonnement est automatique

À l'arrêt de votre module, l'hôte retire vos abonnements. Ne vous en occupez
pas dans `arreter()`.

---

## S'abonner à un événement qui n'existe pas

Ce n'est **pas une erreur**. Le rappel ne sera simplement jamais appelé.

C'est voulu : une version ultérieure peut publier de nouveaux événements sans
que les modules anciens aient à changer, et un module peut s'abonner à un
événement récent tout en restant chargeable sur une version plus ancienne.

```python
#  Fonctionne sur toutes les versions ; n'est appelé que sur celles qui
#  publient cet événement.
self.contexte.abonner("signal.anomalie", self._sur_anomalie)
```

---

## Un exemple complet

Un module qui tient un carnet de bord de la séance :

```python
import json, os, time
from phytoscope.api import (Capacite, Manifeste, Module, SEANCE_COMMENCEE,
                            SEANCE_TERMINEE, EVENEMENT_DETECTE, ALERTE_DISQUE)

class CarnetDeBord(Module):
    MANIFESTE = Manifeste(
        nom="carnet-de-bord",
        titre="Carnet de bord",
        version="1.0.0", api="1.0",
        description="Écrit un journal lisible de ce qui s'est passé.",
        #  Aucune capacité : ce module n'agit que par ses abonnements. C'est
        #  légitime, et le manifeste le dit en n'en déclarant aucune.
    )

    def installer(self):
        self._lignes = []
        self._debut = time.time()
        for evenement, rappel in (
            (SEANCE_COMMENCEE, self._seance_commencee),
            (SEANCE_TERMINEE, self._seance_terminee),
            (EVENEMENT_DETECTE, self._evenement),
            (ALERTE_DISQUE, self._disque),
        ):
            self.contexte.abonner(evenement, rappel)

    def _noter(self, texte):
        self._lignes.append(f"{time.time() - self._debut:8.1f} s  {texte}")

    def _seance_commencee(self, dossier):
        self._noter(f"enregistrement démarré → {os.path.basename(dossier)}")

    def _seance_terminee(self, dossier):
        self._noter("enregistrement terminé")
        self._ecrire(dossier)

    def _evenement(self, instant_s, amplitude_v):
        self._noter(f"événement, {amplitude_v * 1e6:+.1f} µV")

    def _disque(self, megaoctets):
        self._noter(f"ALERTE : {megaoctets:.0f} Mo restants")

    def _ecrire(self, dossier):
        #  Dans NOTRE dossier, pas dans celui de la séance.
        chemin = os.path.join(self.contexte.dossier(),
                              f"carnet-{int(self._debut)}.txt")
        with open(chemin, "w", encoding="utf-8") as f:
            f.write("\n".join(self._lignes) + "\n")
        self.contexte.journal(f"carnet écrit : {chemin}")

    def arreter(self):
        if self._lignes:
            self._ecrire("")
```

---

**Suite :** [5. Éprouver son module](05-essais.md)
