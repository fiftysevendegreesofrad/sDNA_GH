@ECHO OFF
cd dev
set REPO_PATH=%~dp0
start " " "C:\Program Files\Rhino 7\System\Rhino.exe" /nosplash /runscript="-_grasshopper _editor _load _document _open %REPO_PATH%\dev\sDNA_build_components.gh _enter _exit _enterend"
REM start " " "C:\Program Files\Rhino 7\System\Rhino.exe" /nosplash /runscript="-_grasshopper _editor _load _document _open C:\Users\James\Documents\Rhino\Grasshopper\sDNA\source\repos\GHsDNAv0.01\dev\sDNA_build_components.gh _enter _exit _enterend"
cd ..
