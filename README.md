#Para descargar el programa y ejecutarlo tienen que poner en la terminal \n
git clone https://github.com/LoritoAdriel/TP_Final_Biblio.git \n
cd TP_Final_Biblio \n
#Antes de abrir VS lo ejecutan como administrador y ponen \n
Set-ExecutionPolicy -Scope CurrentUser -ExecutionPolicy RemoteSigned \n
python -m venv venv \n
venv\Scripts\activate \n
pip install flask \n
python app.py \n
