rem  ==========================================================================
rem  PhytoScope  attribution  packaging/gabarits/windows/PhytoScope.cmd
rem
rem  Version  : 1.5.1
rem  Date     : 2026-09-18
rem  Editeur  : Bretagne Namaste
rem  Auteur   : Thierry GAYET <Thierry.Gayet@gmail.com>
rem  Site     : https://bretagne-namaste.com
rem  Contact  : contact@bretagne-namaste.com
rem  Licence  : MIT  voir LICENCE.txt
rem
rem  SPDX-License-Identifier: MIT
rem  fin de l'attribution
rem  ==========================================================================

@echo off
rem ==========================================================================
rem   PhytoScope — lanceur Windows
rem
rem   Tout est fourni : l'interpreteur Python, les bibliotheques, le logiciel.
rem   Rien a installer, rien a telecharger. Ce fichier ne fait que designer le
rem   bon interpreteur et lui passer la main.
rem ==========================================================================
setlocal
set "ICI=%~dp0"
set "PYTHON=%ICI%python\pythonw.exe"

if not exist "%PYTHON%" (
    echo PhytoScope : l'interpreteur embarque est introuvable.
    echo Attendu ici : %PYTHON%
    echo Reinstallez le logiciel.
    pause
    exit /b 1
)

rem ---------------------------------------------------------------------------
rem   Cache de bytecode, construit une seule fois
rem ---------------------------------------------------------------------------
rem   Le paquet est livre sans le moindre .pyc : Python recompile alors tous
rem   les modules au demarrage — Qt et NumPy compris — et l'attente se voit,
rem   quelques secondes a chaque lancement si le dossier n'est pas
rem   inscriptible. L'installateur .exe le construit pendant l'installation ;
rem   le .msi et l'archive portable n'ont pas cette occasion, d'ou ce passage.
rem
rem   Le temoin evite de recommencer. Il est ecrit APRES, pour qu'une
rem   compilation interrompue soit reprise au lancement suivant.
set "TEMOIN=%ICI%python\.bytecode-pret"
if not exist "%TEMOIN%" (
    echo Premiere ouverture : preparation du cache de bytecode...
    "%ICI%python\python.exe" -m compileall -q "%ICI%app" >nul 2>&1
    "%ICI%python\python.exe" -m compileall -q "%ICI%python\Lib" >nul 2>&1
    rem  Si le dossier est en lecture seule — Program Files sans droits —, le
    rem  temoin ne s'ecrit pas et l'on retentera. Ce n'est pas bloquant : sans
    rem  cache, le logiciel demarre seulement plus lentement.
    echo pret> "%TEMOIN%" 2>nul
)

rem  pythonw.exe n'ouvre pas de console : c'est ce qu'on veut pour une
rem  application graphique. Le diagnostic, lui, a besoin d'une console et
rem  passe donc par python.exe — voir Diagnostic.cmd.
start "" "%PYTHON%" "%ICI%app\run.py" %*
endlocal
