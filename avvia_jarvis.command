#!/bin/bash
# Questo file apre Jarvis in una finestra di Terminale dedicata.
# Va messo NELLA STESSA CARTELLA di jarvis.py

cd "$(dirname "$0")"
python3 jarvis.py

# tiene aperta la finestra dopo che Jarvis si chiude, così vedi eventuali errori
echo ""
echo "Premi INVIO per chiudere questa finestra..."
read
