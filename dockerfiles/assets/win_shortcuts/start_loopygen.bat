@echo off
setlocal

TITLE Start LooPyGen

set name=loopygen

docker container ls -a | find "loopygen"
If %ERRORLEVEL% NEQ 0 (
    docker start %name%
    docker ps | find "loopygen"
    If %ERRORLEVEL% NEQ 0 (
        START http://localhost:8080
    ) else (
        Echo The container couldn't start, check Docker Desktop!
        pause
        "C:\Program Files\Docker\Docker\Docker Desktop.exe"
    )
) else (
    docker pull sk33z3r/%name%

    set "psCommand="(new-object -COM 'Shell.Application').BrowseForFolder(0,'Please choose a folder.',0,0).self.path""

    for /f "usebackq delims=" %%I in (`powershell %psCommand%`) do set "folder=%%I"

    docker run -d --name %name% -p 8080:80 -v !folder!:/loopygen/collections sk33z3r/%name%

    If %ERRORLEVEL% NEQ 0 (
        START http://localhost:8080
    ) else (
        Echo The container couldn't start, check Docker Desktop!
        pause
        "C:\Program Files\Docker\Docker\Docker Desktop.exe"
    )
)