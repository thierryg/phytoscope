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

rem  pythonw.exe n'ouvre pas de console : c'est ce qu'on veut pour une
rem  application graphique. Le diagnostic, lui, a besoin d'une console et
rem  passe donc par python.exe — voir Diagnostic.cmd.
start "" "%PYTHON%" "%ICI%app\run.py" %*
endlocal
