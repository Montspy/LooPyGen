# cd ui
# python -m virtualenv .
# .\Scripts\activate
# pip install -r requirements.txt

cp ..\css\images\favicon\favicon.ico .
pyinstaller --onefile --clean --windowed --name loopygen_companion --icon=favicon.ico --add-data="favicon.ico;files" main.py