# itu project
#Projekt byl testován na OS windows s pythonem 3.9 a 3.10.
#pro spuštění doporučujeme postupovat takto: --můžete také tento soubor celý zkopírovat do powerShellu
    #vytvoří virtuální prostředí .venv 
    py -m venv .venv
    #aktivuje toto virtuální prostředí
    .venv\Scripts\Activate
    #nainstaluje potřebné moduly
    pip3 install -r requirements.txt
    #nainicializuje databázi
    py database.py -c 
    #spustí aplikaci
    py tmt.py
#lze přeskočit vytváření virtuálního prostředí, avšak dojde k nainstalování modulů ze souboru #requirements.txt na Vašem PC

