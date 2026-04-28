# Installa
python3 -m venv ~/venv/fusionsolar
source ~/venv/fusionsolar/bin/activate
pip install pyhfs request

# Esegui ogni volta per rientrare nell'ambiente
source ~/venv/fusionsolar/bin/activate

# Esegui per chiamare le API
cd ~/xgreen
python fusionsolar_datarealtime_alarmlist.py  
