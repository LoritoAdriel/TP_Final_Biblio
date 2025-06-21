#Para descargar el programa y ejecutarlo tienen que poner en la terminal
git clone https://github.com/LoritoAdriel/TP_Final_Biblio.git
cd TP_Final_Biblio
#Antes de abrir VS lo ejecutan como administrador y ponen
Set-ExecutionPolicy -Scope CurrentUser -ExecutionPolicy RemoteSigned
python -m venv venv
venv\Scripts\activate
pip install flask
python app.py
