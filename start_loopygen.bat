@echo off

TITLE Start LooPyGen

set name=loopygen

docker container ls -a | find "loopygen" && docker start %name% || docker pull sk33z3r/%name%

docker ps | find "loopygen" && START http://localhost:8080 || START https://wiki.ezl2.app && "C:\Program Files\Docker\Docker\Docker Desktop.exe"
