@ECHO OFF
:: Script to tell windows to build our custom image
TITLE Build LooPyMint2

set name="loopymint2"
docker build --tag %name% .