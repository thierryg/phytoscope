rem  ==========================================================================
rem  PhytoScope  attribution  packaging/gabarits/windows/Diagnostic.cmd
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
rem  Controles avant vol, avec une console pour en lire le resultat.
rem  La sortie est aussi ecrite dans un fichier : c'est celui a joindre a un
rem  signalement.
setlocal
set "ICI=%~dp0"
chcp 65001 >nul
"%ICI%python\python.exe" "%ICI%app\run.py" --check
echo.
echo Rapport ecrit dans : %ICI%diagnostic.txt
"%ICI%python\python.exe" "%ICI%app\run.py" --check > "%ICI%diagnostic.txt" 2>&1
pause
endlocal
