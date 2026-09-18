#  ==========================================================================
#  PhytoScope — attribution — packaging/Makefile
#
#  Version  : 1.5.1
#  Date     : 2026-09-18
#  Éditeur  : Bretagne Namasté
#  Auteur   : Thierry GAYET <Thierry.Gayet@gmail.com>
#  Site     : https://bretagne-namaste.com
#  Contact  : contact@bretagne-namaste.com
#  Licence  : MIT — voir LICENCE.txt
#
#  SPDX-License-Identifier: MIT
#  fin de l'attribution
#  ==========================================================================

# ===========================================================================
#  PhytoScope — fabrique des paquets d'installation
#
#  Tout se construit depuis Debian, Ubuntu ou Mint. Une cible par système,
#  et « make tout » pour l'ensemble.
#
#      make outils      ce qui est installé, ce qui manque
#      make deps        installe NSIS et msitools dans ~/.local/opt, sans sudo
#
#      make debian      → .deb                    (Debian, Ubuntu, Mint)
#      make fedora      → .rpm                    (Fedora, RHEL, Rocky, Alma)
#      make windows     → .zip + .exe + .msi      (Windows 10 et 11)
#      make macos       → .zip + .pkg             (Intel et Apple Silicon)
#      make source      → .tar.gz                 (tous systèmes)
#
#      make tout        les cinq, dans l'ordre du plus rapide au plus long
#      make linux       seulement .deb et .rpm
#      make hors-ligne  les paquets qui embarquent leurs bibliothèques
#
#      make verifier    relit et contrôle ce qui a été produit
#      make empreintes  recalcule le fichier .sha256
#      make propre      vide build/paquets
#
#  Licence MIT — Bretagne Namasté — https://bretagne-namaste.com
# ===========================================================================

SHELL      := /bin/sh
.DEFAULT_GOAL := aide

ICI        := $(dir $(abspath $(lastword $(MAKEFILE_LIST))))
RACINE     := $(abspath $(ICI)..)

#  L'interpréteur : celui du logiciel s'il existe — il a PySide6, dont la
#  fabrication des icônes a besoin —, sinon celui du système. Les scripts
#  savent de toute façon retrouver le bon pour le rendu des icônes.
PY         := $(shell test -x "$(RACINE)/src/phytoscope/.venv/bin/python" \
                && echo "$(RACINE)/src/phytoscope/.venv/bin/python" \
                || echo python3)

#  La version vient du fichier VERSION du logiciel — seule source de vérité.
#  On peut l'imposer :  make tout VERSION=1.6.0-rc1
VERSION    ?= $(shell sed -n 's/^ *version *= *//p' \
                "$(RACINE)/src/phytoscope/phytoscope/VERSION" | head -1)

#  L'itération d'empaquetage : elle change quand l'empaquetage change sans que
#  le logiciel bouge.  make tout RELEASE=2
RELEASE    ?= 1

#  Un dossier par invocation de make, horodaté. Il est calculé UNE fois, avec
#  « := », et exporté : sans cela chaque cible créerait le sien, et les
#  paquets d'une même fabrication se retrouveraient éparpillés dans cinq
#  dossiers différents.
HORODATAGE := $(shell date +%Y%m%d-%H%M)
SORTIE     ?= $(RACINE)/build/paquets/$(VERSION)-$(HORODATAGE)
export PHYTOSCOPE_SORTIE := $(SORTIE)

#  Passé à chaque générateur, pour que tous estampillent la même chose.
IDENT      := --version "$(VERSION)" --release "$(RELEASE)"

.PHONY: aide outils deps debian fedora windows macos source tout linux \
        hors-ligne verifier documents empreintes propre version \
        certificat signer empreinte-certificat

aide:
	@echo
	@echo "  PhytoScope $(VERSION) — fabrique des paquets"
	@echo
	@echo "  Préparation"
	@echo "    make outils       ce qui est installé, ce qui manque"
	@echo "    make deps         installe NSIS et msitools sans sudo"
	@echo
	@echo "  Un système"
	@echo "    make debian       .deb        Debian, Ubuntu, Mint"
	@echo "    make fedora       .rpm        Fedora, RHEL, Rocky, Alma"
	@echo "    make windows      .zip .exe .msi"
	@echo "    make macos        .zip .pkg   Intel et Apple Silicon"
	@echo "    make source       .tar.gz     tous systèmes"
	@echo
	@echo "  Plusieurs"
	@echo "    make tout         les cinq"
	@echo "    make linux        .deb et .rpm"
	@echo "    make hors-ligne   avec les bibliothèques embarquées"
	@echo
	@echo "  Signature"
	@echo "    make certificat   cree le certificat (une seule fois)"
	@echo "    make signer       signe les paquets de la fabrication"
	@echo "    make empreinte-certificat   son empreinte SHA-256"
	@echo
	@echo "  Après coup"
	@echo "    make documents    readme, install, licence, changelog, empreintes"
	@echo "    make verifier     relit et contrôle ce qui a été produit"
	@echo "    make empreintes   recalcule le fichier .sha256"
	@echo "    make propre       vide build/paquets"
	@echo
	@echo "  Cette fabrication irait dans :"
	@echo "    $(SORTIE)"
	@echo
	@echo "  On peut imposer :  make tout VERSION=1.6.0 RELEASE=2"
	@echo

version:
	@echo "$(VERSION)"

outils:
	@$(PY) "$(ICI)construire.py" --outils

deps:
	@$(PY) "$(ICI)construire.py" --deps

# --- une cible par système -------------------------------------------------
debian:
	@$(PY) "$(ICI)construire_debian.py" $(IDENT)

fedora:
	@$(PY) "$(ICI)construire_fedora.py" $(IDENT)

windows:
	@$(PY) "$(ICI)construire_windows.py" $(IDENT)

macos:
	@$(PY) "$(ICI)construire_macos.py" $(IDENT)

source:
	@$(PY) "$(ICI)construire_source.py" $(IDENT)

# --- groupes ---------------------------------------------------------------
#  L'ordre n'est pas indifférent : les cibles rapides d'abord, de sorte qu'une
#  panne d'outil se voie en dix secondes plutôt qu'au bout du quart d'heure
#  que demande la compression de l'installateur Windows.
linux: debian fedora

#  L'ordre compte : la signature Authenticode MODIFIE le .exe et le .msi,
#  et les empreintes doivent donc être calculées après elle. « documents »
#  écrit les empreintes ; il vient en dernier.
tout: source linux macos windows certificat signer documents
	@echo
	@echo "  Fabrication terminée : $(SORTIE)"
	@$(PY) "$(ICI)verifier.py" "$(SORTIE)" | tail -n 20
	@echo

hors-ligne:
	@$(PY) "$(ICI)construire_debian.py" $(IDENT) --hors-ligne
	@$(PY) "$(ICI)construire_fedora.py" $(IDENT) --hors-ligne
	@$(PY) "$(ICI)construire_macos.py"  $(IDENT) --hors-ligne
	@$(PY) "$(ICI)construire_windows.py" $(IDENT)

# --- signature -------------------------------------------------------------
#  Le certificat est AUTO-SIGNÉ : il prouve l'intégrité et la continuité
#  d'origine, il ne fait taire ni SmartScreen ni Gatekeeper. Voir signature.py.
certificat:
	@$(PY) "$(ICI)signature.py" --certificat

signer:
	@$(PY) "$(ICI)signature.py" --signer --sortie "$(SORTIE)"

empreinte-certificat:
	@$(PY) "$(ICI)signature.py" --empreinte


# --- après coup ------------------------------------------------------------
documents:
	@$(PY) -c "import sys; sys.path.insert(0, '$(ICI)'); import commun; \
		id_ = commun.Identite.lire('$(VERSION)', '$(RELEASE)'); \
		n = len(commun.ecrire_les_documents(id_)); \
		commun.ecrire_les_empreintes(id_); \
		print(f'  {n} documents et les empreintes écrits')"

verifier:
	@$(PY) "$(ICI)verifier.py" $(if $(wildcard $(SORTIE)),"$(SORTIE)",)
	@$(PY) "$(ICI)signature.py" --verifier --sortie "$(SORTIE)" 2>/dev/null || true

empreintes:
	@$(PY) -c "import sys; sys.path.insert(0, '$(ICI)'); import commun; \
		commun.ecrire_les_empreintes(commun.Identite.lire('$(VERSION)')); \
		print('  empreintes recalculées')"

propre:
	@rm -rf "$(RACINE)/build/paquets"
	@echo "  $(RACINE)/build/paquets vidé"
