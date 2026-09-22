# -*- coding: utf-8 -*-
#  ==========================================================================
#  PhytoScope — attribution — src/phytoscope/phytoscope/__main__.py
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

"""Point d'entrée : `python -m phytoscope`, ou `python run.py`.

Le démarrage suit une séquence stricte, et chaque étape peut échouer
proprement, avec un message qui dit quoi faire :

    1. analyse de la ligne de commande ;
    2. mise en place de la journalisation (fichier, niveau ERROR par défaut) ;
    3. contrôles avant vol : Python, paquets, bibliothèques système,
       répertoires accessibles ;
    4. si quelque chose manque : diagnostic précis et proposition
       d'installation — en console comme en fenêtre ;
    5. chargement des réglages, puis lancement de l'interface ou du mode
       sans interface.

Le point important de l'étape 3 : un paquet Python **installé mais
inutilisable** (bibliothèque système absente) n'est pas un paquet manquant.
Confondre les deux envoie l'utilisateur réinstaller pour rien ce qui est
déjà là.
"""
from __future__ import annotations

import argparse
import os
import sys
from typing import List, Optional

#  La bannière vit dans `core/console.py` : elle y porte la version et
#  l'éditeur, et une seule copie du dessin évite qu'elles divergent. Celle
#  qui était ici avait d'ailleurs perdu un caractère sur son premier trait.


# ---------------------------------------------------------------------------
#  Ligne de commande
# ---------------------------------------------------------------------------
def build_parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(
        prog="phytoscope",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        description="Écoute, mesure et enregistrement des signaux végétaux.",
        epilog="""exemples :
  phytoscope                          lancement normal
  phytoscope --simulation             découverte sans matériel
  phytoscope --check                  contrôles avant vol, puis sortie
  phytoscope --install-missing        installe les paquets manquants
  phytoscope --headless --record --duration 3600
  phytoscope --log-level debug --debug-usb --capture-frames
""")

    g = p.add_argument_group("source")
    g.add_argument("--simulation", action="store_true",
                   help="force le générateur interne (aucun matériel requis)")
    g.add_argument("--device", default=None,
                   help="nom du périphérique d'entrée ou du port série")
    g.add_argument("--rate", type=float, default=None,
                   help="fréquence d'échantillonnage en hertz")

    g = p.add_argument_group("session")
    g.add_argument("--record", action="store_true",
                   help="démarre l'enregistrement dès le lancement")
    g.add_argument("--headless", action="store_true",
                   help="acquisition et enregistrement sans interface")
    g.add_argument("--duration", type=float, default=0.0,
                   help="durée en secondes du mode sans interface (0 = illimité)")
    g.add_argument("--settings", default=None,
                   help="chemin d'un fichier de réglages à charger")
    g.add_argument("--theme", choices=("sombre", "clair", "contraste"),
                   default=None, help="thème de l'interface")
    g.add_argument("--lang", "--langue", dest="lang", default=None,
                   help="langue de l'interface : fr, en, es, pt, it, id, ru, "
                        "zh, ja, ko, ar — ou toute autre présente dans "
                        "phytoscope/langues/")

    g = p.add_argument_group("journalisation et mise au point")
    g.add_argument("--log-level", choices=("error", "warning", "info", "debug"),
                   default=None,
                   help="niveau de journalisation (défaut : error)")
    g.add_argument("--log-file", default=None,
                   help="chemin du fichier de journal")
    g.add_argument("--log-console", action="store_true",
                   help="affiche aussi le journal dans le terminal")
    g.add_argument("--debug", action="store_true",
                   help="mode de mise au point : niveau debug et outils bas niveau")
    g.add_argument("--debug-usb", action="store_true",
                   help="diagnostic USB au démarrage, avec VID/PID")
    g.add_argument("--capture-frames", action="store_true",
                   help="enregistre les trames reçues dans un fichier")
    g.add_argument("--verbose-audio", action="store_true",
                   help="laisse ALSA et JACK écrire sur le terminal "
                        "(par défaut leurs messages vont au journal)")

    g = p.add_argument_group("contrôles")
    g.add_argument("--check", action="store_true",
                   help="exécute les contrôles avant vol et quitte")
    g.add_argument("--install-missing", action="store_true",
                   help="installe les paquets Python manquants, sans poser de question")
    g.add_argument("--no-check", action="store_true",
                   help="saute les contrôles avant vol")
    g.add_argument("--diagnostic", "--diag", action="store_true", dest="diagnostic",
                   help="affiche la checklist complète au démarrage, puis lance "
                        "le logiciel (comportement de « make run »)")
    g.add_argument("--no-diagnostic", action="store_true",
                   help="démarre sans afficher le bilan")
    g.add_argument("--version", action="store_true", help="affiche la version")
    return p


# ---------------------------------------------------------------------------
#  Séquence de démarrage
# ---------------------------------------------------------------------------
def main(argv: Optional[List[str]] = None) -> int:
    #  Avant tout affichage : sans cela, une sortie redirigée sous Windows
    #  lèverait `UnicodeEncodeError` au premier caractère accentué.
    from .core.console import forcer_utf8
    forcer_utf8()

    args = build_parser().parse_args(argv)

    # -- 1. version, sans rien charger d'autre ------------------------------
    if args.version:
        from .version import (AUTHOR_EMAIL, AUTHOR_NAME, AUTHORS, CONTACT,
                              FULL_TITLE, RELEASE_DATE, WEBSITE)
        print(f"{FULL_TITLE} — {RELEASE_DATE}")
        print(f"{AUTHORS}")
        print(f"{WEBSITE} · {CONTACT}"
              + (f" · {AUTHOR_EMAIL}" if AUTHOR_EMAIL else ""))
        return 0

    # -- 2. journalisation ---------------------------------------------------
    from .config import Settings
    from .core import console as C
    from .core.errors import ExitCode
    from .core.logging_setup import install_excepthook, setup as setup_logging

    #  Tout ce qui vient de la ligne de commande passe par « forcer » : la
    #  valeur vaut pour cette séance, et le fichier de réglages n'en garde rien.
    settings = Settings.load(args.settings)
    if args.debug:
        settings.forcer("logging", "level", "DEBUG")
        settings.forcer("diagnostics", "debug_mode", True)
    if args.log_level:
        settings.forcer("logging", "level", args.log_level.upper())
    if args.log_file:
        settings.forcer("logging", "directory",
                        os.path.dirname(os.path.abspath(args.log_file)))
        settings.forcer("logging", "filename", os.path.basename(args.log_file))
    if args.log_console:
        settings.forcer("logging", "to_console", True)
    if args.capture_frames:
        settings.forcer("diagnostics", "capture_usb_frames", True)
        settings.forcer("diagnostics", "debug_mode", True)

    chemin_journal = setup_logging(settings)
    install_excepthook()

    # Les couches audio bas niveau écrivent en C sur la sortie d'erreur ; on
    # détourne leurs messages vers le journal avant d'ouvrir le moindre flux.
    if getattr(settings.audio_out, "quiet", True) and not args.verbose_audio:
        from .core.audio_quiet import installer as installer_silencieux
        installer_silencieux()
    from .core.logging_setup import get_logger
    log = get_logger(__name__)
    log.info("Démarrage — arguments : %s", vars(args))

    # -- 3. contrôles avant vol ---------------------------------------------
    from . import VERSION
    from .core import preflight
    from .version import AUTHOR
    rapport = None
    if not args.no_check:
        rapport = preflight.run(settings)
        besoin_interface = not (args.headless or args.check)

        if args.check:
            print(C.banniere(VERSION, AUTHOR))
            from .core.platform_info import detect as detecter_systeme
            systeme = detecter_systeme()
            print(C.discret(f"  {systeme.libelle()} — famille "
                            f"{systeme.famille or 'indéterminée'}"))
            preflight.resoudre_en_console(rapport, interactif=False)
            if chemin_journal:
                print(C.discret(f"  Journal : {chemin_journal}"))
            for conseil in rapport.conseils():
                print("  " + C.info("→ ") + conseil)
            print(C.discret("  Détail des paquets système : make system-deps"))
            print()
            return int(ExitCode.OK if rapport.peut_demarrer
                       else ExitCode.DEPENDANCE_MANQUANTE)

        if args.install_missing:
            paquets = rapport.paquets_a_installer(tous=True)
            if paquets:
                print(C.info(f"Installation de : {' '.join(paquets)}"))
                preflight.installer(paquets, env=rapport.env)
                rapport = preflight.run(settings)

        pret = (rapport.peut_demarrer if besoin_interface
                else rapport.peut_demarrer_sans_interface)
        if not pret:
            print(C.banniere(VERSION, AUTHOR))
            if not preflight.resoudre_en_console(rapport, interactif=True):
                _rappel_final(rapport, chemin_journal)
                return int(ExitCode.DEPENDANCE_MANQUANTE)
            rapport = preflight.run(settings)
        elif rapport.casses or rapport.absents:
            # Le logiciel démarre, mais amputé : on le dit une fois, sans bloquer.
            for r in rapport.casses:
                print(C.alerte(f"  ! {r.requirement.module} est installé mais "
                               f"inutilisable ({r.bibliotheque_manquante or 'erreur'}) "
                               f"— {r.requirement.role} indisponible."))
            cmd = rapport.commande_systeme()
            if cmd:
                print(C.discret("    Remède : ") + C.info(cmd))
                print()

    # -- 4. options de ligne de commande sur les réglages -------------------
    if args.simulation:
        settings.forcer("acquisition", "source", "simulation")
    if args.device:
        settings.forcer("acquisition", "device", args.device)
        if settings.acquisition.source == "auto":
            settings.forcer("acquisition", "source", "audio")
    if args.rate:
        settings.forcer("acquisition", "sample_rate", args.rate)
    if args.record:
        settings.forcer("recording", "auto_start", True)
    if args.theme:
        settings.forcer("ui", "theme", args.theme)
    if args.lang:
        settings.forcer("ui", "language", args.lang)

    # La langue doit être choisie AVANT de construire quoi que ce soit : les
    # libellés sont traduits à la construction, pas à l'affichage.
    from .i18n import definir_langue
    retenue = definir_langue(settings.ui.language)
    if retenue != settings.ui.language:
        #  Langue inconnue : on travaille en français pour cette séance, sans
        #  réécrire pour autant le choix de l'utilisateur.
        settings.forcer("ui", "language", retenue)

    # -- 5. checklist de démarrage -------------------------------------------
    #  Affichée PAR DÉFAUT. C'était l'inverse : il fallait « --diagnostic »
    #  pour la voir, et l'on démarrait donc le plus souvent sans savoir sur
    #  quel interpréteur, quelle carte ni quelle sortie audio on travaillait.
    #  « --no-diagnostic » la supprime pour qui n'en veut pas.
    if not args.no_diagnostic:
        _bilan(settings, rapport)
        #  Les contrôles avant vol avec elle : la checklist dit « toutes
        #  présentes », le détail dit lesquelles et en quelle version. C'est
        #  ce détail que réclame tout signalement d'anomalie.
        if rapport is not None:
            print(rapport.to_console())
            print()

    if args.debug_usb or settings.diagnostics.debug_mode:
        try:
            from .core import usbdiag
            print(usbdiag.diagnose(settings).as_text())
            print()
        except Exception as exc:                       # noqa: BLE001
            log.error("Diagnostic USB impossible : %s", exc)

    # -- 6. lancement --------------------------------------------------------
    if args.headless:
        return _headless(settings, args.duration)
    return _graphique(settings, rapport, langue_imposee=bool(args.lang))


def _bilan(settings, rapport=None) -> None:
    """Bilan compact affiché au lancement — l'état réel, en une page.

    Six blocs, dans l'ordre où l'on se pose les questions : quelle machine,
    quelles briques logicielles, quel matériel branché, quelles entrées et
    sorties sonores, où vont les fichiers, où va le journal. Tenir sur un
    écran est une contrainte : au-delà, personne ne lit.
    """
    from . import FULL_NAME
    from .core import console as C
    from .core.logging_setup import log_path
    from .core.platform_info import detect as detecter_systeme

    from . import VERSION
    from .version import AUTHOR

    ligne = "─" * 74
    #  La bannière remplace le pavé que `run.py` écrivait autrefois sur la
    #  sortie d'erreur quand il écartait un interpréteur : elle sépare
    #  franchement ce que PhytoScope raconte de ce qui précède dans le
    #  terminal, et donne la version sans qu'on la cherche — c'est le premier
    #  renseignement que demande tout signalement d'anomalie.
    print(C.banniere(VERSION, AUTHOR))
    print(C.titre(f"  {FULL_NAME} — checklist"))
    print(C.discret("  " + ligne))

    # 1. machine
    systeme = detecter_systeme()
    print(C.ligne_statut("info", "Système", systeme.libelle(), 20))
    print(C.ligne_statut("info", "Python", f"{sys.version.split()[0]}  "
                         f"({'environnement virtuel' if hasattr(sys, 'base_prefix') and sys.base_prefix != sys.prefix else 'interpréteur système'})", 20))

    # 2. briques logicielles
    if rapport is not None:
        manquants = [r.requirement.module for r in rapport.absents]
        casses = [r.requirement.module for r in rapport.casses]
        if not manquants and not casses:
            print(C.ligne_statut("ok", "Dépendances", "toutes présentes", 20))
        else:
            detail = []
            if casses:
                detail.append(f"{len(casses)} inutilisable(s) : " + ", ".join(casses))
            if manquants:
                detail.append(f"{len(manquants)} absente(s) : " + ", ".join(manquants))
            print(C.ligne_statut("warn", "Dépendances", " · ".join(detail), 20))

    # 3. matériel
    try:
        from .core import usbdiag
        carte = usbdiag.find_phytosense((settings.diagnostics.expected_vid,
                                         settings.diagnostics.expected_pid))
        if carte is not None:
            print(C.ligne_statut("ok", "Carte PhytoSense", carte.describe(), 20))
        else:
            connus = [d for d in usbdiag.enumerate_devices(include_audio=False)
                      if d.known_as]
            if connus:
                print(C.ligne_statut("warn", "Carte PhytoSense",
                                     "absente — mais " + connus[0].known_as, 20))
            else:
                print(C.ligne_statut("warn", "Carte PhytoSense",
                                     "absente — repli sur le générateur interne", 20))
    except Exception as exc:                           # noqa: BLE001
        print(C.ligne_statut("warn", "Carte PhytoSense", f"non vérifiée ({exc})", 20))

    # 4. audio
    try:
        from .core.audio_quiet import sans_bavardage
        with sans_bavardage():
            import sounddevice as sd
            peripheriques = sd.query_devices()
        entrees = [d["name"] for d in peripheriques
                   if d.get("max_input_channels", 0) > 0]
        sorties = [d["name"] for d in peripheriques
                   if d.get("max_output_channels", 0) > 0]
        print(C.ligne_statut("ok" if entrees else "warn", "Entrées audio",
                             f"{len(entrees)} — {entrees[0][:38] if entrees else 'aucune'}", 20))
        print(C.ligne_statut("ok" if sorties else "warn", "Sorties audio",
                             f"{len(sorties)} — {sorties[0][:38] if sorties else 'aucune'}", 20))
    except Exception:
        print(C.ligne_statut("warn", "Audio", "indisponible — écoute désactivée", 20))

    # 5. source retenue et réglages saillants
    a, m = settings.acquisition, settings.music
    print(C.ligne_statut("info", "Source demandée",
                         f"{a.source} · {a.sample_rate:g} Hz · "
                         f"{max(a.channels, 1)} voie(s)", 20))
    print(C.ligne_statut("info", "Musique",
                         f"{m.scale} sur {m.root} · {m.diapason_hz:g} Hz · "
                         f"{m.instrument}", 20))

    # 6. fichiers
    print(C.ligne_statut("info", "Séances", settings.recording.directory, 20))
    print(C.ligne_statut("info", "Journal",
                         f"{log_path() or '(aucun)'}  [{settings.logging.level}]", 20))
    print(C.discret("  " + ligne))
    if rapport is not None and rapport.commande_systeme():
        print("  " + C.alerte("Bibliothèques système manquantes : ")
              + C.info(rapport.commande_systeme()))
    print(C.discret("  Diagnostic détaillé : make sanity   ·   "
                    "sans cette checklist : run.py --no-diagnostic"))
    print()
    # L'interface va prendre la main pour des heures : si la sortie est
    # redirigée vers un fichier, elle est bloquée en tampon et l'utilisateur
    # ne verrait ce bilan qu'à la fermeture. On vide donc explicitement.
    #  `sys.stdout` vaut `None` quand Windows lance un point d'entrée
    #  graphique (`gui-scripts`), qui n'a pas de console attachée.
    if sys.stdout is not None:
        sys.stdout.flush()


def _rappel_final(rapport, chemin_journal: str) -> None:
    from .core import console as C
    print()
    print(C.erreur("  Le logiciel ne peut pas démarrer."))
    for conseil in rapport.conseils():
        print("  " + C.info("→ ") + conseil)
    if chemin_journal:
        print(C.discret(f"  Détails dans : {chemin_journal}"))
    print()


# ---------------------------------------------------------------------------
#  Interface graphique
# ---------------------------------------------------------------------------
def _graphique(settings, rapport=None, langue_imposee: bool = False) -> int:
    from .core import console as C
    from .core.errors import ExitCode
    from .core.logging_setup import get_logger
    log = get_logger(__name__)

    try:
        from PySide6.QtWidgets import QApplication
    except BaseException as exc:                       # noqa: BLE001
        from .core.preflight import analyser_import_casse, interpreteur_etranger
        lib, paquet, cmd, presente = analyser_import_casse(str(exc))
        print()
        print(C.erreur("  L'interface graphique ne peut pas se charger."))
        if lib and presente:
            #  Rien ne manque sur la machine : c'est cet interpréteur-ci qui
            #  ne voit pas les bibliothèques du système. Conseiller un
            #  « apt install » ici ferait réinstaller un paquet déjà présent.
            venu_de = interpreteur_etranger()
            print(f"  {C.alerte(lib)} est bien installée sur ce système, mais "
                  f"l'interpréteur qui exécute PhytoScope ne l'atteint pas.")
            print(f"  Interpréteur : {C.info(sys.executable)}")
            if venu_de:
                print(f"  Il vient de {C.alerte(venu_de)} — un interpréteur "
                      f"installé hors du système a son propre chemin de")
                print("  recherche et ne lit pas celui de la distribution.")
            print(C.discret("  Il n'y a aucun paquet à installer."))
            print("  Remède : lancer PhytoScope par l'environnement du projet,")
            print("  " + C.info("cd src/phytoscope && make run") +
                  C.discret("   (ou .venv/bin/python run.py)"))
        elif lib:
            print(f"  PySide6 est installé, mais la bibliothèque système "
                  f"{C.alerte(lib)} est introuvable.")
            if cmd:
                print("  Remède : " + C.info(cmd))
        else:
            print(f"  {exc}")
        print(C.discret("  Vous pouvez travailler sans interface : "
                        "phytoscope --headless --record"))
        print()
        log.critical("Chargement de Qt impossible : %s", exc)
        return int(ExitCode.DEPENDANCE_MANQUANTE)

    app = QApplication(sys.argv[:1])

    #  La langue, au tout premier démarrage et jamais ensuite. Les
    #  installateurs .run, .exe et .app la demandent déjà ; apt et dnf, eux,
    #  installent sans rien demander — c'est ce qu'on attend d'eux —, et ce
    #  passage couvre ces deux cas ainsi que le lancement depuis les sources.
    #
    #  Avant `_appliquer_langue_qt` : la langue retenue ici doit être celle
    #  que Qt applique, pas la précédente.
    if getattr(settings, "premier_lancement", False) and not langue_imposee:
        try:
            from .ui.language_dialog import demander_si_premier_lancement
            retenue = demander_si_premier_lancement(settings)
            if retenue and retenue != settings.ui.language:
                settings.ui.language = retenue
                from .i18n import definir_langue
                definir_langue(retenue)
            #  Écrit tout de suite : un logiciel fermé brutalement juste après
            #  reposerait la question, ce qui est le genre de détail qui use.
            settings.save()
        except Exception as exc:                       # noqa: BLE001
            #  Une question de langue ne doit jamais empêcher de démarrer.
            log.error("Choix de la langue impossible : %s", exc)

    _appliquer_langue_qt(app, settings)
    # Dès maintenant, et non après la construction de la fenêtre : un Ctrl+C
    # pendant un démarrage qui traîne doit aboutir lui aussi.
    from .core.interrupt import ajouter_nettoyage, installer as installer_ctrl_c
    installer_ctrl_c(app)
    app.setApplicationName("PhytoScope")
    app.setOrganizationName("Bretagne Namaste")
    app.setApplicationDisplayName("PhytoScope")
    try:
        from .ui.icon import app_icon
        app.setWindowIcon(app_icon())
    except Exception:                                  # pragma: no cover
        log.debug("Icône indisponible", exc_info=True)

    ecran = None
    try:
        from .ui.splash import Splash
        ecran = Splash(settings.ui.theme)
        ecran.show()
        ecran.etape("contrôles avant vol…")
        app.processEvents()
    except Exception:                                  # pragma: no cover
        log.debug("Écran d'accueil indisponible", exc_info=True)

    # Fenêtre de démarrage : n'apparaît que s'il y a quelque chose à dire.
    if rapport is not None and (rapport.casses or rapport.absents):
        try:
            from .ui.startup_dialog import StartupDialog
            dlg = StartupDialog(rapport, settings)
            if not dlg.exec_si_necessaire():
                log.info("Démarrage annulé depuis la fenêtre de contrôle.")
                return int(ExitCode.OK)
        except Exception as exc:                       # noqa: BLE001
            log.error("Fenêtre de contrôle indisponible : %s", exc)

    try:
        from .ui.main_window import MainWindow
        if ecran is not None:
            ecran.etape("construction de l'interface…")
        window = MainWindow(settings, splash=ecran)
        ajouter_nettoyage(window.arret_immediat)
        window.show()
        if ecran is not None:
            ecran.terminer(window)
        return app.exec()
    except Exception as exc:                           # noqa: BLE001
        log.critical("Erreur fatale au lancement de l'interface", exc_info=True)
        try:
            from PySide6.QtWidgets import QMessageBox
            QMessageBox.critical(None, "PhytoScope — erreur fatale",
                                 f"{exc}\n\nDétails dans le journal.")
        except Exception:                              # pragma: no cover
            print(C.erreur(f"Erreur fatale : {exc}"))
        return int(ExitCode.ERREUR_GENERALE)


def _appliquer_langue_qt(app, settings) -> None:
    """Sens de lecture et traduction des fenêtres standard de Qt.

    Deux choses que le catalogue maison ne peut pas faire : inverser toute la
    mise en page pour une langue qui s'écrit de droite à gauche — l'arabe —, et
    traduire les boutons des fenêtres de dialogue fournies par Qt (« Ouvrir »,
    « Annuler », le sélecteur de fichiers). La seconde est facultative : si les
    traductions de Qt ne sont pas installées sur la machine, ces boutons
    restent en anglais, ce qui n'empêche rien.
    """
    from .core.logging_setup import get_logger
    from .i18n import direction_courante, langue_courante
    log = get_logger(__name__)
    try:
        from PySide6.QtCore import QLibraryInfo, QLocale, QTranslator, Qt
    except Exception:                                  # pragma: no cover
        return

    if direction_courante() == "rtl":
        app.setLayoutDirection(Qt.RightToLeft)

    code = langue_courante()
    try:
        chemin = QLibraryInfo.path(QLibraryInfo.TranslationsPath)
        for nom in (f"qtbase_{code}", f"qt_{code}"):
            tr = QTranslator(app)
            if tr.load(nom, chemin):
                app.installTranslator(tr)
                log.debug("Traductions Qt chargées : %s", nom)
                break
        QLocale.setDefault(QLocale(code))
    except Exception as exc:                           # noqa: BLE001
        log.debug("Traductions Qt indisponibles : %s", exc)


# ---------------------------------------------------------------------------
#  Mode sans interface
# ---------------------------------------------------------------------------
def _headless(settings, duration: float) -> int:
    """Acquisition sans interface — séances longues, machines sans écran."""
    import time

    from . import FULL_NAME
    from .core import console as C
    from .core.engine import Engine
    from .core.errors import ExitCode
    from .core.logging_setup import get_logger, log_path

    log = get_logger(__name__)
    print(C.titre(f"  {FULL_NAME} — mode sans interface"))
    print(C.discret(f"  Journal : {log_path() or '(aucun)'}"))
    print()

    from .core.interrupt import installer as installer_ctrl_c
    installer_ctrl_c()          # Ctrl+C, SIGTERM, et arrêt forcé au second

    engine = Engine(settings)
    engine.on_message = lambda t: print("  " + C.info("·") + " " + t)
    try:
        engine.start()
    except Exception as exc:                           # noqa: BLE001
        log.critical("Démarrage impossible", exc_info=True)
        print(C.erreur(f"  Démarrage impossible : {exc}"))
        return int(ExitCode.MATERIEL_ABSENT)

    chemin = engine.start_recording()
    if chemin:
        print(C.succes(f"  Enregistrement : {chemin}"))
    else:
        print(C.alerte("  Enregistrement impossible : acquisition seule."))
    print(C.discret("  Ctrl+C pour arrêter proprement "
                    "(deux fois de suite : arrêt immédiat)."))
    print()

    code = ExitCode.OK
    t0 = time.time()
    try:
        while duration <= 0 or time.time() - t0 < duration:
            time.sleep(1.0)
            st = engine.state
            drapeau = C.erreur(" SAT") if st.saturated else "    "
            print(f"\r  {st.elapsed_s:8.1f} s  {st.value_v * 1e6:+9.1f} µV  "
                  f"{st.rms_v * 1e6:7.2f} µV eff.  "
                  f"{st.events_total:5d} évén.  {st.notes_total:5d} notes{drapeau}",
                  end="", flush=True)
    except KeyboardInterrupt:
        print("\n  " + C.alerte("Interruption demandée."))
        code = ExitCode.INTERROMPU
    except Exception as exc:                           # noqa: BLE001
        log.critical("Erreur pendant l'acquisition", exc_info=True)
        print("\n  " + C.erreur(f"Erreur : {exc}"))
        code = ExitCode.ERREUR_GENERALE
    finally:
        print()
        try:
            engine.stop()
        except Exception:                              # pragma: no cover
            log.exception("Arrêt imparfait")
        try:
            settings.save()
        except Exception:                              # pragma: no cover
            pass
    print(C.succes("  Séance close proprement."))
    return int(code)


if __name__ == "__main__":
    sys.exit(main())
