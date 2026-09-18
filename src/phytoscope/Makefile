#  ==========================================================================
#  PhytoScope — attribution — src/phytoscope/Makefile
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

# ============================================================================
#  PhytoScope — Makefile
#
#  Cibles principales :
#      make            affiche cette aide
#      make install    crée l'environnement virtuel et installe les dépendances
#      make run        lance le logiciel
#      make demo       lance le logiciel en mode simulation (sans matériel)
#      make test       exécute les tests
#      make check      vérifie la syntaxe et l'état des dépendances
#      make clean      supprime les fichiers temporaires
#      make distclean  supprime aussi l'environnement virtuel
#
#  Fonctionne sous GNU/Linux, macOS et Windows (avec Git Bash ou WSL).
#  Sous Windows en invite de commandes native, utilisez make.bat.
# ============================================================================

SHELL     := /bin/sh

# ---------------------------------------------------------------------------
#  Choix de l'interpréteur
#
#  Sous GNU/Linux, le Python de Homebrew embarque sa propre glibc et ne sait
#  pas charger les bibliothèques du système (libGL, libportaudio…) : un
#  environnement virtuel bâti dessus donne une interface graphique qui ne
#  démarre pas. On préfère donc l'interpréteur de la distribution, sauf si
#  l'utilisateur impose le sien :  make install PYTHON=/chemin/vers/python3
# ---------------------------------------------------------------------------
DEFAULT_PYTHON := $(shell sh tools/pick_python.sh 2>/dev/null)
PYTHON    ?= $(if $(DEFAULT_PYTHON),$(DEFAULT_PYTHON),python3)
VENV      ?= .venv
REQ       := requirements.txt
REQ_OPT   := requirements-optionnel.txt
REQ_DEV   := requirements-dev.txt

# Emplacement des exécutables du venv, selon le système
ifeq ($(OS),Windows_NT)
  BIN := $(VENV)/Scripts
  PY  := $(BIN)/python.exe
else
  BIN := $(VENV)/bin
  PY  := $(BIN)/python
endif

PIP := $(PY) -m pip

.DEFAULT_GOAL := help
.PHONY: help install install-dev system-deps sanity run run-silencieux demo headless test check lint \
        clean distclean freeze doctor version bump-patch bump-minor bump-major \
        release-check dist tag release

# ---------------------------------------------------------------------------
help:
	@echo ""
	@echo "  PhytoScope — écoute et mesure des signaux végétaux"
	@echo "  -------------------------------------------------"
	@echo ""
	@echo "  make install       environnement virtuel + dépendances (à faire une fois)"
	@echo "  make run           lance le logiciel"
	@echo "  make demo          lance le logiciel sans matériel (plante simulée)"
	@echo "  make headless      enregistre une séance sans interface graphique"
	@echo "  make test          exécute les tests"
	@echo "  make doctor        diagnostic : ce qui est installé, ce qui manque"
	@echo "  make clean         nettoie les fichiers temporaires"
	@echo ""
	@echo "  make system-deps   paquets système de votre distribution"
	@echo "  make sanity        contrôles avant vol (dépendances, bibliothèques)"
	@echo ""

# ---------------------------------------------------------------------------
#  Installation
# ---------------------------------------------------------------------------
$(VENV):
	@echo "→ interpréteur retenu : $(PYTHON)  ($$($(PYTHON) -V 2>&1))"
	@echo "→ création de l'environnement virtuel dans $(VENV)"
	$(PYTHON) -m venv $(VENV)
	$(PIP) install --upgrade pip setuptools wheel

install: $(VENV)          ## installe les dépendances d'exécution
	@echo "→ installation des dépendances ($(REQ))"
	$(PIP) install -r $(REQ)
	@echo "→ dépendances facultatives ($(REQ_OPT)) — leur échec est sans gravité"
	-$(PIP) install -r $(REQ_OPT)
	@echo ""
	@echo "✓ Installation terminée. Lancez :  make run"

install-dev: $(VENV)      ## installe aussi les outils de développement
	$(PIP) install -r $(REQ_DEV)

system-deps:              ## paquets système de VOTRE distribution
	$(PYTHON) tools/system_deps.py

sanity: $(VENV)           ## contrôles avant vol (dépendances, bibliothèques)
	$(PY) run.py --check

freeze:                   ## fige les versions réellement installées
	$(PIP) freeze > requirements.lock.txt
	@echo "✓ requirements.lock.txt écrit"

# ---------------------------------------------------------------------------
#  Exécution
# ---------------------------------------------------------------------------
run: $(VENV)              ## bilan de démarrage, puis lance le logiciel
	@$(PY) run.py --diagnostic || \
	  (echo ""; echo "→ Diagnostic détaillé :  make sanity"; exit 1)

run-silencieux: $(VENV)   ## lance le logiciel sans le bilan
	@$(PY) run.py --no-diagnostic

demo: $(VENV)             ## lance le logiciel avec la plante simulée
	$(PY) run.py --simulation --diagnostic

headless: $(VENV)         ## enregistre 3600 s sans interface graphique
	$(PY) run.py --headless --record --duration 3600

# ---------------------------------------------------------------------------
#  Qualité
# ---------------------------------------------------------------------------
test: $(VENV)             ## exécute les tests
	$(PY) -m pytest tests -q

lint: $(VENV)             ## analyse statique (si ruff est installé)
	-$(PY) -m ruff check phytoscope tests

check:                    ## vérifie la syntaxe sans rien installer
	$(PYTHON) tools/check_syntax.py

doctor:                   ## dit ce qui est installé et ce qui manque
	$(PYTHON) tools/doctor.py

# ---------------------------------------------------------------------------
#  Publication
# ---------------------------------------------------------------------------
version:                  ## affiche la version courante
	$(PYTHON) tools/release.py show

bump-patch:               ## incrémente le numéro de correctif
	$(PYTHON) tools/release.py bump patch

bump-minor:               ## incrémente le numéro mineur
	$(PYTHON) tools/release.py bump minor

bump-major:               ## incrémente le numéro majeur
	$(PYTHON) tools/release.py bump major

release-check:            ## vérifie que la version est diffusable
	$(PYTHON) tools/release.py check

dist: release-check       ## fabrique les archives .tar.gz et .zip
	$(PYTHON) tools/release.py dist

tag:                      ## pose l'étiquette git de la version
	$(PYTHON) tools/release.py tag

release: dist tag         ## chaîne complète de publication
	@echo "✓ version publiée dans dist/"

# ---------------------------------------------------------------------------
#  Nettoyage
# ---------------------------------------------------------------------------
clean:                    ## supprime les fichiers temporaires
	find . -name "__pycache__" -type d -exec rm -rf {} + 2>/dev/null || true
	find . -name "*.pyc" -delete 2>/dev/null || true
	rm -rf .pytest_cache .ruff_cache build dist *.egg-info

distclean: clean          ## supprime aussi l'environnement virtuel
	rm -rf $(VENV)
