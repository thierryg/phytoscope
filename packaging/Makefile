#  ==========================================================================
#  PhytoScope — attribution — packaging/Makefile
#
#  Version   : 1.6.0
#  Date      : 2026-09-23
#  Publisher : Bretagne Namasté
#  Author    : Thierry GAYET <Thierry.Gayet@gmail.com>
#  Website   : https://bretagne-namaste.com
#  Contact   : contact@bretagne-namaste.com
#  License   : MIT — see LICENSE.txt
#
#  SPDX-License-Identifier: MIT
#  end of attribution
#  ==========================================================================

# ===========================================================================
#  PhytoScope — the installation-package factory
#
#  Everything builds from Debian, Ubuntu or Mint. One target per system, and
#  "make all" for the lot.
#
#      make tools       what is installed, what is missing
#      make deps        installs NSIS and msitools in ~/.local/opt, no sudo
#
#      make debian      → .deb                    (Debian, Ubuntu, Mint)
#      make fedora      → .rpm                    (Fedora, RHEL, Rocky, Alma)
#      make windows     → .zip + .exe + .msi      (Windows 10 and 11)
#      make macos       → .zip + .pkg             (Intel and Apple Silicon)
#      make source      → .tar.gz                 (every system)
#
#      make all         the five, fastest first
#      make linux       .deb and .rpm only
#      make offline     the packages that carry their own libraries
#
#      make verify      reopens and checks what was produced
#      make checksums   recomputes the .sha256 file
#      make clean       empties build/packages
#
#  MIT licence — Bretagne Namasté — https://bretagne-namaste.com
# ===========================================================================

SHELL      := /bin/sh
#  It said "aide" until 2026-09-23 — a target that had not existed since the
#  rename of 2026-09-22. A bare `make` died on "No rule to make target
#  'aide'": the one invocation a newcomer types first.
.DEFAULT_GOAL := help

HERE       := $(dir $(abspath $(lastword $(MAKEFILE_LIST))))
RACINE     := $(abspath $(HERE)..)

#  L'interpréteur : celui du logiciel s'il existe — il a PySide6, dont la
#  fabrication des icônes a besoin —, sinon celui du système. Les scripts
#  savent de toute façon retrouver le bon pour le rendu des icônes.
PY         := $(shell test -x "$(RACINE)/src/phytoscope/.venv/bin/python" \
                && echo "$(RACINE)/src/phytoscope/.venv/bin/python" \
                || echo python3)

#  La version vient du fichier VERSION du logiciel — seule source de vérité.
#  On peut l'imposer :  make all VERSION=1.6.0-rc1
VERSION    ?= $(shell sed -n 's/^ *version *= *//p' \
                "$(RACINE)/src/phytoscope/phytoscope/VERSION" | head -1)

#  L'itération d'empaquetage : elle change quand l'empaquetage change sans que
#  le logiciel bouge.  make all RELEASE=2
RELEASE    ?= 1

#  One directory per invocation of make, timestamped. It is computed ONCE,
#  with ":=", and exported: without that each target would make its own, and
#  the packages of one fabrication would end up scattered across five
#  different directories.
#
#  SORTIE is still honoured: it was the documented name until 2026-09-23, and
#  somebody's habit is not a reason to break their command line.
TIMESTAMP  := $(shell date +%Y%m%d-%H%M)
OUTPUT     ?= $(if $(SORTIE),$(SORTIE),$(RACINE)/build/packages/$(VERSION)-$(TIMESTAMP))
export PHYTOSCOPE_OUTPUT := $(OUTPUT)

#  The directory the AFTER-THE-FACT targets work on — documents, verify,
#  checksums, sign. It is not $(OUTPUT).
#
#  $(OUTPUT) carries this invocation's timestamp, so on a bare `make verify`
#  it names a directory that does not exist; `dossier_fabrication()` then
#  CREATED it and repointed `latest` at it. Running `make verify` after a
#  build therefore destroyed the very thing it was meant to check — the empty
#  new build became `latest` (found 2026-09-23).
#
#  Resolved lazily, with `=`, so each rule asks at the moment it runs:
#    · a directory given on the command line wins — that is what it is for;
#    · else, if this invocation's own $(OUTPUT) exists, we are inside a build
#      that created it, and that is the one to work on;
#    · else fall back to the existing `latest`.
LATEST_LINK := $(RACINE)/build/packages/latest
#  On ONE line, and wrapped in $(strip): a `\`-continued assignment joins its
#  lines with a space, and those spaces end up inside the value — which is
#  how the first attempt handed verify.py a path with two leading blanks.
TARGET_DIR = $(strip $(if $(filter command line,$(origin OUTPUT) $(origin SORTIE)),$(OUTPUT),$(if $(wildcard $(OUTPUT)),$(OUTPUT),$(shell test -d "$(LATEST_LINK)" && readlink -f "$(LATEST_LINK)" || echo "$(OUTPUT)"))))

#  Passé à chaque générateur, pour que tous estampillent la même chose.
IDENT      := --version "$(VERSION)" --release "$(RELEASE)"

.PHONY: help tools deps debian fedora windows macos source all linux \
        offline firmware deliverables verify documents checksums clean version \
        certificate certificate-status certificate-verify \
        certificate-renew sign certificate-fingerprint

help:
	@echo
	@echo "  PhytoScope $(VERSION) — package factory"
	@echo
	@echo "  Preparation"
	@echo "    make tools                    what is installed, what is missing"
	@echo "    make deps                     install NSIS and msitools, no sudo"
	@echo
	@echo "  One system"
	@echo "    make debian                   .deb        Debian, Ubuntu, Mint"
	@echo "    make fedora                   .rpm        Fedora, RHEL, Rocky, Alma"
	@echo "    make windows                  .zip .exe .msi"
	@echo "    make macos                    .zip .pkg   Intel and Apple Silicon"
	@echo "    make source                   .tar.gz     every system"
	@echo
	@echo "  Several"
	@echo "    make all                      all five"
	@echo "    make linux                    .deb and .rpm"
	@echo "    make offline                  with the libraries bundled"
	@echo
	@echo "  Firmware"
	@echo "    make firmware                 build the .uf2 and file it with the rest"
	@echo "    make deliverables             the packages AND the firmware"
	@echo
	@echo "  Signing"
	@echo "    make certificate              create it, and fill certificate/"
	@echo "    make certificate-status       what exists, and where"
	@echo "    make certificate-verify       do both copies agree?"
	@echo "    make certificate-renew        REPLACE the key (breaks the link)"
	@echo "    make sign                     sign this build's packages"
	@echo "    make certificate-fingerprint  its SHA-256 fingerprint"
	@echo
	@echo "  Afterwards"
	@echo "    make documents                readme, install, licence, changelog, checksums"
	@echo "    make verify                   reopen and check what was produced"
	@echo "    make checksums                recompute the .sha256 file"
	@echo "    make clean                    empty build/packages"
	@echo
	@echo "  This build would go to:"
	@echo "    $(OUTPUT)"
	@echo
	@echo "  You can force:  make all VERSION=1.6.0 RELEASE=2"
	@echo

version:
	@echo "$(VERSION)"

tools:
	@$(PY) "$(HERE)build.py" --outils

deps:
	@$(PY) "$(HERE)build.py" --deps

# --- une cible par système -------------------------------------------------
debian:
	@$(PY) "$(HERE)build_debian.py" $(IDENT)

fedora:
	@$(PY) "$(HERE)build_fedora.py" $(IDENT)

windows:
	@$(PY) "$(HERE)build_windows.py" $(IDENT)

macos:
	@$(PY) "$(HERE)build_macos.py" $(IDENT)

source:
	@$(PY) "$(HERE)build_source.py" $(IDENT)

# --- firmware --------------------------------------------------------------
#  Deliberately OUTSIDE `all`: building the firmware needs an ARM
#  cross-toolchain that the packaging machine may not have, and a `make all`
#  that failed for want of `arm-none-eabi-gcc` would be an unpleasant
#  surprise. The target exists for whoever wants both at once.
#
#  OUTPUT is handed to it, so the deliverable is filed in the SAME build as
#  the .deb and the .msi.
firmware:
	@PHYTOSCOPE_OUTPUT="$(OUTPUT)" "$(RACINE)/src/firmware/build.sh"

#  The packages AND the firmware, in one build.
#
#  `documents` runs AGAIN at the end, and that is not redundant: `all` writes
#  the six documents and the checksums into each system directory, and
#  `firmware` then creates `Firmware/` — which would have none of them.
#  `make verify` rejected exactly that, so every `make deliverables` produced
#  a build its own checker refused (found 2026-09-23). C-2O asks that a
#  directory copied on its own still make sense; the firmware's is a
#  deliverable like the others.
deliverables: all firmware
	@$(MAKE) --no-print-directory documents OUTPUT="$(OUTPUT)"
	@echo
	@echo "  Packages and firmware: $(OUTPUT)"

# --- groupes ---------------------------------------------------------------
#  L'ordre n'est pas indifférent : les cibles rapides d'abord, de sorte qu'une
#  panne d'outil se voie en dix secondes plutôt qu'au bout du quart d'heure
#  que demande la compression de l'installateur Windows.
linux: debian fedora

#  L'ordre compte : la signature Authenticode MODIFIE le .exe et le .msi,
#  et les empreintes doivent donc être calculées après elle. « documents »
#  écrit les empreintes ; il vient en dernier.
all: source linux macos windows certificate sign documents
	@echo
	@echo "  Fabrication terminée : $(OUTPUT)"
	@$(PY) "$(HERE)verify.py" "$(OUTPUT)" | tail -n 20
	@echo

offline:
	@$(PY) "$(HERE)build_debian.py" $(IDENT) --offline
	@$(PY) "$(HERE)build_fedora.py" $(IDENT) --offline
	@$(PY) "$(HERE)build_macos.py"  $(IDENT) --offline
	@$(PY) "$(HERE)build_windows.py" $(IDENT)

# --- signature -------------------------------------------------------------
#  Le certificat est AUTO-SIGNÉ : il prouve l'intégrité et la continuité
#  d'origine, il ne fait taire ni SmartScreen ni Gatekeeper. Voir signature.py.
#  Le certificat de signature. `certificate.py` est le point d'entrée : il
#  appelle `signature.py` pour la cryptographie, et remplit `certificate/`.
certificate:
	@$(PY) "$(HERE)certificate.py" --creer

certificate-status:
	@$(PY) "$(HERE)certificate.py"

certificate-verify:
	@$(PY) "$(HERE)certificate.py" --verifier

#  REMPLACE la clé : rompt le lien avec tout ce qui a déjà été signé.
#  Demande une confirmation explicite, et refuse sans terminal.
certificate-renew:
	@$(PY) "$(HERE)certificate.py" --refaire

sign:
	@$(PY) "$(HERE)signature.py" --signer --sortie "$(TARGET_DIR)"

certificate-fingerprint:
	@$(PY) "$(HERE)signature.py" --empreinte


# --- après coup ------------------------------------------------------------
documents:
	@PHYTOSCOPE_OUTPUT="$(TARGET_DIR)" $(PY) -c "import sys; sys.path.insert(0, '$(HERE)'); import common; \
		id_ = common.Identite.lire('$(VERSION)', '$(RELEASE)'); \
		n = len(common.ecrire_les_documents(id_)); \
		common.ecrire_les_empreintes(id_); \
		print(f'  {n} documents et les empreintes écrits')"

verify:
	@$(PY) "$(HERE)verify.py" "$(TARGET_DIR)"
	@$(PY) "$(HERE)signature.py" --verifier --sortie "$(TARGET_DIR)" 2>/dev/null || true

checksums:
	@PHYTOSCOPE_OUTPUT="$(TARGET_DIR)" $(PY) -c "import sys; sys.path.insert(0, '$(HERE)'); import common; \
		common.ecrire_les_empreintes(common.Identite.lire('$(VERSION)')); \
		print('  empreintes recalculées')"

clean:
	@rm -rf "$(RACINE)/build/packages"
	@echo "  $(RACINE)/build/packages emptied"
