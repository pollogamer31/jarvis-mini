"""
JARVIS MINI - Assistente da terminale
--------------------------------------
Un piccolo assistente testuale ispirato a Jarvis.
Scrivi comandi e lui ti risponde, apre siti, fa calcoli, ecc.

REQUISITI:
    pip3 install rich deep-translator langdetect

Per il comando "chiedi" serve anche Ollama installato e aperto sul Mac
(scaricabile gratis da ollama.com), con un modello scaricato, es:
    ollama pull llama3.2

COME SI USA:
    python3 jarvis.py
    poi scrivi "aiuto" per vedere tutti i comandi
"""

import datetime
import random
import webbrowser
import time
import os
import threading
import subprocess
import json
import urllib.request

from rich.console import Console
from rich.panel import Panel
from rich.text import Text

from deep_translator import GoogleTranslator
from langdetect import detect

console = Console()

# ---------------------------------------------------------
# DATI DELL'ASSISTENTE (personalizza qui!)
# ---------------------------------------------------------

NOME_ASSISTENTE = "JARVIS"
NOME_UTENTE = "Lore"

FILE_LOG = "jarvis_log.txt"
FILE_COMPITI = "compiti.txt"
FILE_SCADENZE = "scadenze.txt"

# se il log supera questa lunghezza, viene "tagliato" tenendo solo le righe più recenti
LIMITE_RIGHE_LOG = 500
RIGHE_LOG_DA_TENERE = 200

SUONO_AVVISO = "/System/Library/Sounds/Glass.aiff"

# indirizzi e modello di Ollama, il "cervello" AI che gira in locale sul Mac
INDIRIZZO_OLLAMA_GENERATE = "http://localhost:11434/api/generate"
INDIRIZZO_OLLAMA_CHAT = "http://localhost:11434/api/chat"
MODELLO_OLLAMA = "llama3.2"

ORA_ACCENSIONE = datetime.datetime.now()

# variabili globali per il pomodoro (servono per poterlo fermare da un altro comando)
STOP_STUDIO = threading.Event()
THREAD_STUDIO = None

# variabili globali per la modalità chat con l'AI
MODALITA_CHAT_ATTIVA = False
CRONOLOGIA_CHAT = []

DISCOGRAFIA = [
    ("Gli occhi della tigre", "Nayt"),
    ("Come un film", "Nayt"),
    ("Habitat", "Nayt"),
    ("Lasciami stare", "Nayt"),
    ("Immortale", "Nayt"),
    ("Da zero", "Nayt"),
    ("Il ragazzo d'oro", "Guè"),
    ("Bravo ragazzo", "Guè"),
    ("Chico", "Guè"),
    ("Veleno", "Guè"),
    ("Piango Sulla Lambo", "Guè"),
    ("Spacco tutto", "Guè (Club Dogo)"),
    ("Ventidue", "22Simba"),
    ("Per i Roiz", "22Simba"),
    ("Spoiler", "22Simba"),
    ("Stare Bene", "22Simba"),
    ("Speranza", "22Simba"),
    ("King del Rap", "Marracash"),
    ("Badabum Cha Cha", "Marracash"),
    ("Crudelia - I nervi", "Marracash"),
    ("15 piani", "Marracash"),
    ("Bravi a cadere", "Marracash"),
    ("Grammelot", "Kid Yugi"),
    ("Sturm und Drang", "Kid Yugi"),
    ("Il Filmografo", "Kid Yugi"),
    ("Il ferro di Čechov", "Kid Yugi"),
    ("Sintetico", "Kid Yugi"),
    ("Berserker", "Kid Yugi"),
]

SITI_RAPIDI = {
    "youtube": "https://youtube.com",
    "roblox": "https://www.roblox.com/create",
    "github": "https://github.com",
    "instagram": "https://instagram.com",
    "chatgpt": "https://chat.openai.com",
    "claude": "https://claude.ai",
}

# banner ASCII mostrato all'avvio, con effetto "digitazione" e sfumatura di colore
BANNER_ASCII = [
    r"      _         _______      _______  _____ ",
    r"     | |  /\   |  __ \ \    / /_   _|/ ____|",
    r"     | | /  \  | |__) \ \  / /  | | | (___  ",
    r" _   | |/ /\ \ |  _  / \ \/ /   | |  \___ \ ",
    r"| |__| / ____ \| | \ \  \  /   _| |_ ____) |",
    r" \____/_/    \_\_|  \_\  \/   |_____|_____/ ",
]

COLORI_BANNER = ["blue3", "dodger_blue2", "deep_sky_blue1", "cyan2", "bright_cyan", "white"]


def mostra_banner():
    for riga, colore in zip(BANNER_ASCII, COLORI_BANNER):
        for carattere in riga:
            console.print(carattere, end="", style=f"bold {colore}")
            time.sleep(0.0015)
        console.print()
    console.print("[dim italic]        >> assistente personale di Lore <<[/]\n")


# ---------------------------------------------------------
# FUNZIONI DI BASE
# ---------------------------------------------------------

def saluta():
    ora = datetime.datetime.now().hour
    if ora < 6:
        momento = "Sei sveglio a quest'ora?"
    elif ora < 13:
        momento = "Buongiorno"
    elif ora < 18:
        momento = "Buon pomeriggio"
    else:
        momento = "Buonasera"
    console.print(f"[bold cyan]{momento}, {NOME_UTENTE}.[/] Sono {NOME_ASSISTENTE}, dimmi pure.")


def dimmi_ora():
    adesso = datetime.datetime.now()
    console.print(f"[green]Sono le {adesso.strftime('%H:%M')} di {adesso.strftime('%A %d %B %Y')}[/]")


def apri_sito(comando):
    parole = comando.split()
    if len(parole) < 2:
        console.print("[red]Dimmi quale sito, tipo: apri youtube[/]")
        return
    nome = parole[1].lower()
    if nome in SITI_RAPIDI:
        console.print(f"[cyan]Apro {nome}...[/]")
        webbrowser.open(SITI_RAPIDI[nome])
    else:
        console.print(f"[yellow]Non conosco '{nome}', provo a cercarlo su Google...[/]")
        webbrowser.open(f"https://www.google.com/search?q={nome}")


def calcolatrice(comando):
    espressione = comando.replace("calcola", "", 1).strip()
    try:
        caratteri_ammessi = set("0123456789+-*/(). ")
        if not set(espressione) <= caratteri_ammessi:
            raise ValueError
        risultato = eval(espressione)
        console.print(f"[green]Risultato: {risultato}[/]")
    except Exception:
        console.print("[red]Non ho capito il calcolo, scrivi tipo: calcola 4*7+2[/]")


def ascolta_random():
    canzone, artista = random.choice(DISCOGRAFIA)
    console.print(f"[magenta]🎧 Oggi ascolta: \"{canzone}\" di {artista}[/]")


def suona_beep():
    try:
        os.system(f"afplay {SUONO_AVVISO}")
    except Exception:
        pass


def mostra_stato():
    adesso = datetime.datetime.now()
    durata = adesso - ORA_ACCENSIONE
    secondi_totali = int(durata.total_seconds())
    minuti = secondi_totali // 60
    secondi = secondi_totali % 60
    if minuti == 0:
        testo_durata = f"{secondi} secondi"
    else:
        testo_durata = f"{minuti} minuti e {secondi} secondi"
    console.print(f"[cyan]Sono acceso da {testo_durata}.[/]")


def scrivi_nel_log(comando):
    adesso = datetime.datetime.now()
    riga = f"[{adesso.strftime('%d/%m/%Y %H:%M:%S')}] {comando}\n"
    with open(FILE_LOG, "a", encoding="utf-8") as file:
        file.write(riga)


def pulisci_log_se_troppo_grande():
    if not os.path.exists(FILE_LOG):
        return
    with open(FILE_LOG, "r", encoding="utf-8") as file:
        righe = file.readlines()
    if len(righe) > LIMITE_RIGHE_LOG:
        righe_da_tenere = righe[-RIGHE_LOG_DA_TENERE:]
        with open(FILE_LOG, "w", encoding="utf-8") as file:
            file.writelines(righe_da_tenere)


# ---------------------------------------------------------
# TIMER FLESSIBILE (unisce timer + promemoria in un comando solo)
# ---------------------------------------------------------

UNITA_IN_SECONDI = {
    "sec": 1, "s": 1, "secondi": 1, "secondo": 1,
    "min": 60, "m": 60, "minuti": 60, "minuto": 60,
    "h": 3600, "ora": 3600, "ore": 3600,
}


def analizza_tempo(parole):
    totale_secondi = 0
    trovato_qualcosa = False
    resto = list(parole)

    while len(resto) >= 2:
        possibile_unita = resto[-1].lower()
        possibile_numero = resto[-2]
        if possibile_unita in UNITA_IN_SECONDI and possibile_numero.isdigit():
            totale_secondi += int(possibile_numero) * UNITA_IN_SECONDI[possibile_unita]
            trovato_qualcosa = True
            resto = resto[:-2]
        else:
            break

    if not trovato_qualcosa:
        return None, None

    testo_rimanente = " ".join(resto)
    return totale_secondi, testo_rimanente


def formatta_durata(secondi_totali):
    ore = secondi_totali // 3600
    resto = secondi_totali % 3600
    minuti = resto // 60
    secondi = resto % 60
    parti = []
    if ore > 0:
        parti.append(f"{ore} h")
    if minuti > 0:
        parti.append(f"{minuti} min")
    if secondi > 0 or not parti:
        parti.append(f"{secondi} sec")
    return " ".join(parti)


def avvisa_dopo(testo, secondi):
    time.sleep(secondi)
    suona_beep()
    console.print(f"\n[bold yellow]🔔 {testo}[/]")


def timer(comando):
    parole = comando.split()[1:]
    if not parole:
        console.print("[red]Usa: timer 2 min 3 sec  (oppure con testo: timer controlla il forno 10 min)[/]")
        return

    secondi, testo = analizza_tempo(parole)

    if secondi is None or secondi <= 0:
        console.print("[red]Formato non riconosciuto. Usa: timer 1 h 2 min 3 sec[/]")
        return

    messaggio_finale = testo if testo else "Tempo scaduto!"

    if testo:
        console.print(f"[cyan]⏳ Timer impostato tra {formatta_durata(secondi)}: {testo}[/]")
    else:
        console.print(f"[cyan]⏳ Timer partito: {formatta_durata(secondi)}[/]")

    thread = threading.Thread(target=avvisa_dopo, args=(messaggio_finale, secondi), daemon=True)
    thread.start()


# ---------------------------------------------------------
# COMPITI (to-do list semplice, senza data)
# ---------------------------------------------------------

def compiti_lista():
    if not os.path.exists(FILE_COMPITI):
        console.print("[yellow]Nessun compito salvato. Aggiungine uno con: compiti aggiungi <testo>[/]")
        return
    with open(FILE_COMPITI, "r", encoding="utf-8") as file:
        righe = file.readlines()
    if not righe:
        console.print("[yellow]La lista dei compiti è vuota.[/]")
        return
    console.print("[bold]I tuoi compiti:[/]")
    for indice, riga in enumerate(righe, start=1):
        console.print(f"  {indice}. {riga.strip()}")


def compiti_aggiungi(testo):
    if testo == "":
        console.print("[red]Dimmi cosa aggiungere, tipo: compiti aggiungi latino pag 40[/]")
        return
    with open(FILE_COMPITI, "a", encoding="utf-8") as file:
        file.write(testo + "\n")
    console.print(f"[green]Aggiunto: {testo}[/]")


def compiti_fatto(numero_testo):
    if not numero_testo.isdigit():
        console.print("[red]Dimmi il numero del compito, tipo: compiti fatto 2[/]")
        return
    numero = int(numero_testo)
    if not os.path.exists(FILE_COMPITI):
        console.print("[yellow]Non ci sono compiti salvati.[/]")
        return
    with open(FILE_COMPITI, "r", encoding="utf-8") as file:
        righe = file.readlines()
    indice = numero - 1
    if indice < 0 or indice >= len(righe):
        console.print("[red]Numero non valido, controlla con: compiti lista[/]")
        return
    rimosso = righe.pop(indice)
    with open(FILE_COMPITI, "w", encoding="utf-8") as file:
        file.writelines(righe)
    console.print(f"[green]✅ Completato e rimosso: {rimosso.strip()}[/]")


def gestisci_compiti(comando):
    parole = comando.split(maxsplit=2)
    if len(parole) < 2:
        console.print("[red]Usa: compiti lista / compiti aggiungi <testo> / compiti fatto <numero>[/]")
        return
    sottocomando = parole[1].lower()
    if sottocomando == "lista":
        compiti_lista()
    elif sottocomando == "aggiungi":
        testo = parole[2] if len(parole) > 2 else ""
        compiti_aggiungi(testo)
    elif sottocomando == "fatto":
        numero = parole[2] if len(parole) > 2 else ""
        compiti_fatto(numero)
    else:
        console.print("[red]Usa: compiti lista / compiti aggiungi <testo> / compiti fatto <numero>[/]")


# ---------------------------------------------------------
# SCADENZE (come i compiti, ma con una data e ordinate per urgenza)
# ---------------------------------------------------------

def interpreta_data(testo):
    try:
        if testo.count("/") == 2:
            return datetime.datetime.strptime(testo, "%d/%m/%Y")
        elif testo.count("/") == 1:
            anno_corrente = datetime.datetime.now().year
            return datetime.datetime.strptime(f"{testo}/{anno_corrente}", "%d/%m/%Y")
    except ValueError:
        return None
    return None


def descrivi_giorni(giorni):
    if giorni < 0:
        return f"SCADUTA da {-giorni} giorni"
    elif giorni == 0:
        return "OGGI"
    elif giorni == 1:
        return "domani"
    else:
        return f"tra {giorni} giorni"


def carica_scadenze():
    if not os.path.exists(FILE_SCADENZE):
        return []
    scadenze = []
    with open(FILE_SCADENZE, "r", encoding="utf-8") as file:
        for riga in file:
            if "|" not in riga:
                continue
            data_testo, testo = riga.strip().split("|", 1)
            try:
                data = datetime.datetime.strptime(data_testo, "%d/%m/%Y")
                scadenze.append((data, testo))
            except ValueError:
                continue
    return scadenze


def salva_scadenze(scadenze):
    with open(FILE_SCADENZE, "w", encoding="utf-8") as file:
        for data, testo in scadenze:
            file.write(f"{data.strftime('%d/%m/%Y')}|{testo}\n")


def scadenza_aggiungi(resto):
    parole = resto.split()
    if len(parole) < 2:
        console.print("[red]Usa: scadenza aggiungi <testo> <gg/mm> , tipo: scadenza aggiungi verifica latino 10/07[/]")
        return
    data_testo = parole[-1]
    testo = " ".join(parole[:-1])
    data = interpreta_data(data_testo)
    if data is None:
        console.print("[red]Data non valida, usa il formato gg/mm oppure gg/mm/aaaa[/]")
        return
    scadenze = carica_scadenze()
    scadenze.append((data, testo))
    salva_scadenze(scadenze)
    console.print(f"[green]Aggiunta scadenza: {testo} ({data.strftime('%d/%m/%Y')})[/]")


def scadenza_lista():
    scadenze = carica_scadenze()
    if not scadenze:
        console.print("[yellow]Nessuna scadenza salvata.[/]")
        return
    scadenze.sort(key=lambda coppia: coppia[0])
    oggi = datetime.datetime.now().date()
    console.print("[bold]Le tue scadenze:[/]")
    for indice, (data, testo) in enumerate(scadenze, start=1):
        giorni = (data.date() - oggi).days
        console.print(f"  {indice}. {testo} - {data.strftime('%d/%m/%Y')} ({descrivi_giorni(giorni)})")


def scadenza_fatto(numero_testo):
    if not numero_testo.isdigit():
        console.print("[red]Dimmi il numero, tipo: scadenza fatto 1[/]")
        return
    numero = int(numero_testo)
    scadenze = carica_scadenze()
    scadenze.sort(key=lambda coppia: coppia[0])
    indice = numero - 1
    if indice < 0 or indice >= len(scadenze):
        console.print("[red]Numero non valido, controlla con: scadenza lista[/]")
        return
    rimossa = scadenze.pop(indice)
    salva_scadenze(scadenze)
    console.print(f"[green]✅ Rimossa: {rimossa[1]}[/]")


def prossima_scadenza():
    scadenze = carica_scadenze()
    if not scadenze:
        console.print("[yellow]Nessuna scadenza salvata.[/]")
        return
    scadenze.sort(key=lambda coppia: coppia[0])
    data, testo = scadenze[0]
    oggi = datetime.datetime.now().date()
    giorni = (data.date() - oggi).days
    console.print(f"[cyan]📌 Prossima scadenza: {testo} - {data.strftime('%d/%m/%Y')} ({descrivi_giorni(giorni)})[/]")


def gestisci_scadenze(comando):
    parole = comando.split(maxsplit=2)
    if len(parole) < 2:
        console.print("[red]Usa: scadenza lista / scadenza aggiungi <testo> <gg/mm> / scadenza fatto <numero>[/]")
        return
    sottocomando = parole[1].lower()
    if sottocomando == "lista":
        scadenza_lista()
    elif sottocomando == "aggiungi":
        resto = parole[2] if len(parole) > 2 else ""
        scadenza_aggiungi(resto)
    elif sottocomando == "fatto":
        numero = parole[2] if len(parole) > 2 else ""
        scadenza_fatto(numero)
    else:
        console.print("[red]Usa: scadenza lista / scadenza aggiungi <testo> <gg/mm> / scadenza fatto <numero>[/]")


# ---------------------------------------------------------
# COUNTDOWN (calcolo veloce, non si salva su file)
# ---------------------------------------------------------

def countdown(comando):
    parole = comando.split()
    if len(parole) < 3:
        console.print("[red]Usa: countdown <nome evento> <gg/mm/aaaa>, tipo: countdown fine scuola 07/06/2027[/]")
        return
    data_testo = parole[-1]
    nome = " ".join(parole[1:-1])
    data = interpreta_data(data_testo)
    if data is None:
        console.print("[red]Data non valida, usa il formato gg/mm oppure gg/mm/aaaa[/]")
        return
    oggi = datetime.datetime.now().date()
    giorni = (data.date() - oggi).days
    if giorni < 0:
        console.print(f"[yellow]{nome} è passato da {-giorni} giorni.[/]")
    elif giorni == 0:
        console.print(f"[bold green]{nome} è oggi! 🎉[/]")
    else:
        console.print(f"[cyan]Mancano {giorni} giorni a \"{nome}\" ({data.strftime('%d/%m/%Y')}).[/]")


# ---------------------------------------------------------
# POMODORO (studio a cicli, personalizzabile, gira in background)
# ---------------------------------------------------------

def aspetta_o_interrompi(secondi):
    for _ in range(secondi):
        if STOP_STUDIO.is_set():
            return
        time.sleep(1)


def ciclo_pomodoro(minuti_studio, minuti_pausa):
    while not STOP_STUDIO.is_set():
        aspetta_o_interrompi(minuti_studio * 60)
        if STOP_STUDIO.is_set():
            break
        suona_beep()
        console.print(f"\n[bold yellow]⏸️  Pausa! Riposati {minuti_pausa} minuti.[/]")

        aspetta_o_interrompi(minuti_pausa * 60)
        if STOP_STUDIO.is_set():
            break
        suona_beep()
        console.print(f"\n[bold green]📚 Si riparte! Studio per {minuti_studio} minuti.[/]")


def avvia_pomodoro(comando):
    global THREAD_STUDIO

    if THREAD_STUDIO is not None and THREAD_STUDIO.is_alive():
        console.print("[yellow]Un pomodoro è già in corso. Scrivi 'stop studio' per fermarlo prima.[/]")
        return

    numeri = [parola for parola in comando.split() if parola.isdigit()]
    if len(numeri) >= 2:
        minuti_studio = int(numeri[0])
        minuti_pausa = int(numeri[1])
    else:
        minuti_studio, minuti_pausa = 25, 5

    STOP_STUDIO.clear()
    console.print(
        f"[cyan]📚 Pomodoro avviato: {minuti_studio} min di studio / {minuti_pausa} min di pausa. "
        f"Scrivi 'stop studio' per fermarlo.[/]"
    )
    THREAD_STUDIO = threading.Thread(target=ciclo_pomodoro, args=(minuti_studio, minuti_pausa), daemon=True)
    THREAD_STUDIO.start()


def ferma_pomodoro():
    if THREAD_STUDIO is None or not THREAD_STUDIO.is_alive():
        console.print("[yellow]Nessun pomodoro attivo al momento.[/]")
        return
    STOP_STUDIO.set()
    console.print("[cyan]Pomodoro fermato.[/]")


# ---------------------------------------------------------
# CHIEDI (risposte vere tramite AI locale, con Ollama)
# streaming vero: la risposta appare parola per parola, esattamente
# come quando usi "ollama run" direttamente dal terminale
# ---------------------------------------------------------

def stampa_streaming_ollama(corpo_richiesta, indirizzo, chiave_testo):
    # chiave_testo indica dove si trova il pezzo di testo nella risposta JSON:
    # "response" per l'endpoint /api/generate, "message" per l'endpoint /api/chat
    risposta_completa = ""
    try:
        richiesta = urllib.request.Request(
            indirizzo,
            data=corpo_richiesta,
            headers={"Content-Type": "application/json"},
        )
        console.print("[bold green]🤖 [/]", end="")
        with urllib.request.urlopen(richiesta, timeout=120) as risposta_http:
            for riga in risposta_http:
                riga = riga.strip()
                if not riga:
                    continue
                pezzo = json.loads(riga)

                if chiave_testo == "response":
                    frammento = pezzo.get("response", "")
                else:
                    frammento = pezzo.get("message", {}).get("content", "")

                if frammento:
                    console.print(frammento, end="", style="green")
                    risposta_completa += frammento

                if pezzo.get("done"):
                    break
        console.print()
        return risposta_completa

    except Exception:
        console.print(
            "\n[red]Non riesco a contattare Ollama. "
            "Controlla che l'app Ollama sia aperta sul Mac e riprova.[/]"
        )
        return None


def chiedi_domanda_singola(domanda):
    if domanda == "":
        console.print("[red]Fammi una domanda, tipo: chiedi cos'è la fotosintesi[/]")
        return
    corpo_richiesta = json.dumps({
        "model": MODELLO_OLLAMA,
        "prompt": domanda,
        "stream": True,
    }).encode("utf-8")
    stampa_streaming_ollama(corpo_richiesta, INDIRIZZO_OLLAMA_GENERATE, "response")


def avvia_chat():
    global MODALITA_CHAT_ATTIVA, CRONOLOGIA_CHAT
    MODALITA_CHAT_ATTIVA = True
    CRONOLOGIA_CHAT = []
    console.print("[cyan]💬 Chat con l'AI avviata: scrivi normalmente, senza bisogno di 'chiedi' davanti.[/]")
    console.print("[dim](scrivi 'chiedi stop' per uscire dalla chat)[/]")


def ferma_chat():
    global MODALITA_CHAT_ATTIVA
    MODALITA_CHAT_ATTIVA = False
    console.print("[cyan]Chat terminata, sei tornato ai comandi normali di Jarvis.[/]")


def invia_messaggio_chat(testo):
    global CRONOLOGIA_CHAT
    if testo == "":
        return
    CRONOLOGIA_CHAT.append({"role": "user", "content": testo})
    corpo_richiesta = json.dumps({
        "model": MODELLO_OLLAMA,
        "messages": CRONOLOGIA_CHAT,
        "stream": True,
    }).encode("utf-8")
    risposta = stampa_streaming_ollama(corpo_richiesta, INDIRIZZO_OLLAMA_CHAT, "message")
    if risposta is not None:
        CRONOLOGIA_CHAT.append({"role": "assistant", "content": risposta})
    else:
        # se la richiesta fallisce, tolgo il messaggio dell'utente dalla cronologia
        CRONOLOGIA_CHAT.pop()


# ---------------------------------------------------------
# TRADUZIONE (italiano <-> inglese autodetect, + latino)
# ---------------------------------------------------------

def traduci(comando):
    resto = comando.replace("traduci", "", 1).strip()
    if resto == "":
        console.print("[red]Usa: traduci <testo> oppure traduci lat/latin <testo>[/]")
        return

    parole = resto.split(maxsplit=1)
    prefisso = parole[0].lower()

    try:
        if prefisso == "lat" and len(parole) > 1:
            risultato = GoogleTranslator(source="it", target="la").translate(parole[1])
            console.print(f"[cyan]🏛️ LATINO: {risultato}[/]")
            return

        if prefisso == "latin" and len(parole) > 1:
            risultato = GoogleTranslator(source="la", target="it").translate(parole[1])
            console.print(f"[cyan]🇮🇹 ITALIANO: {risultato}[/]")
            return

        lingua = detect(resto)
        if lingua == "en":
            risultato = GoogleTranslator(source="en", target="it").translate(resto)
            console.print(f"[cyan]🇮🇹 ITALIANO: {risultato}[/]")
        else:
            risultato = GoogleTranslator(source="it", target="en").translate(resto)
            console.print(f"[cyan]🇬🇧 ENGLISH: {risultato}[/]")

    except Exception:
        console.print("[red]Errore nella traduzione. Controlla la connessione internet.[/]")


# ---------------------------------------------------------
# DADO, MONETA, BATTERIA, SCREENSHOT
# ---------------------------------------------------------

def tira_dado():
    risultato = random.randint(1, 6)
    console.print(f"[cyan]🎲 Hai tirato: {risultato}[/]")


def lancia_moneta():
    risultato = random.choice(["Testa", "Croce"])
    console.print(f"[cyan]🪙 È uscito: {risultato}[/]")


def mostra_batteria():
    try:
        risultato = subprocess.run(["pmset", "-g", "batt"], capture_output=True, text=True)
        for riga in risultato.stdout.split("\n"):
            if "%" in riga:
                console.print(f"[green]🔋 {riga.strip()}[/]")
                return
        console.print("[yellow]Non sono riuscito a leggere la batteria.[/]")
    except Exception:
        console.print("[red]Comando disponibile solo su macOS.[/]")


def fai_screenshot():
    try:
        adesso = datetime.datetime.now()
        nome_file = f"jarvis_screenshot_{adesso.strftime('%Y%m%d_%H%M%S')}.png"
        percorso = os.path.expanduser(f"~/Desktop/{nome_file}")
        subprocess.run(["screencapture", percorso])
        suona_beep()
        console.print(f"[green]📸 Screenshot salvato sulla Scrivania: {nome_file}[/]")
    except Exception:
        console.print("[red]Errore durante lo screenshot (funziona solo su macOS).[/]")


def mostra_aiuto():
    testo = """
[bold underline]⏱️  Gestione del tempo[/]
  timer <tempo> (testo)   -> es: timer 2 min 3 sec  /  timer controlla il forno 10 min
  compiti lista/aggiungi/fatto  -> gestisce i compiti senza data
  scadenza lista/aggiungi/fatto -> gestisce scadenze con data, es: scadenza aggiungi verifica 10/07
  countdown <nome> <data> -> giorni mancanti a un evento, es: countdown fine scuola 07/06/2027
  prossima                -> ti dice solo la scadenza più vicina

[bold underline]🤖 Intelligenza artificiale (serve Ollama aperto)[/]
  chiedi <domanda>        -> fa una domanda singola all'AI locale
  chiedi start            -> apre una chat continua con l'AI (scrivi senza 'chiedi')
  chiedi stop             -> chiude la chat e torna ai comandi normali

[bold underline]📚 Scuola[/]
  traduci <testo>         -> traduce IT<->EN in automatico
  traduci lat <testo>     -> traduce italiano -> latino
  traduci latin <testo>   -> traduce latino -> italiano
  studio (min) (pausa)    -> pomodoro, es: studio 20 4 (default 25 5)
  stop studio             -> ferma il pomodoro in corso

[bold underline]🎧 Svago[/]
  ascolta                 -> ti consiglia una canzone a caso da ascoltare
  dado                    -> tira un dado a 6 facce
  moneta                  -> lancia una moneta (testa/croce)
  calcola <espr>          -> es: calcola 5*3+2

[bold underline]🌐 Web & sistema[/]
  apri <sito>             -> apre youtube / roblox / github / instagram / claude / chatgpt
  ora                     -> ti dice data e ora
  batteria                -> mostra la batteria del Mac
  screenshot              -> fa uno screenshot e lo salva sulla Scrivania

[bold underline]⚙️  Generali[/]
  stato                   -> ti dice da quanto tempo sono acceso
  aiuto                   -> questa lista
  esci                    -> chiude Jarvis
"""
    console.print(Panel(testo, title=f"{NOME_ASSISTENTE} - guida", border_style="cyan"))


# ---------------------------------------------------------
# CICLO PRINCIPALE
# ---------------------------------------------------------

# ---------------------------------------------------------
# CICLO PRINCIPALE
# ---------------------------------------------------------

def esegui_comando(comando):
    # esegue un comando "conosciuto" da Jarvis. Ritorna True se l'ha capito,
    # False se non corrisponde a nessun comando esistente
    if comando == "ora":
        dimmi_ora()
    elif comando.startswith("apri"):
        apri_sito(comando)
    elif comando.startswith("calcola"):
        calcolatrice(comando)
    elif comando == "ascolta":
        ascolta_random()
    elif comando.startswith("timer"):
        timer(comando)
    elif comando == "stop studio":
        ferma_pomodoro()
    elif comando.startswith("studio"):
        avvia_pomodoro(comando)
    elif comando.startswith("compiti"):
        gestisci_compiti(comando)
    elif comando.startswith("scadenza"):
        gestisci_scadenze(comando)
    elif comando.startswith("countdown"):
        countdown(comando)
    elif comando == "prossima":
        prossima_scadenza()
    elif comando.startswith("traduci"):
        traduci(comando)
    elif comando == "dado":
        tira_dado()
    elif comando == "moneta":
        lancia_moneta()
    elif comando == "batteria":
        mostra_batteria()
    elif comando == "screenshot":
        fai_screenshot()
    elif comando == "stato":
        mostra_stato()
    elif comando in ("aiuto", "help"):
        mostra_aiuto()
    else:
        return False
    return True


def main():
    os.system("clear")
    pulisci_log_se_troppo_grande()
    mostra_banner()
    saluta()
    console.print("[dim](scrivi 'aiuto' in qualsiasi momento per vedere i comandi)[/]")

    while True:
        comando = console.input("\n[bold yellow]>> [/]").strip().lower()

        if comando == "":
            continue

        scrivi_nel_log(comando)

        # se siamo in modalità chat, tutto quello che scrivi (tranne uscire)
        # viene mandato direttamente all'AI, senza bisogno di scrivere "chiedi"
        if MODALITA_CHAT_ATTIVA and comando not in ("chiedi stop", "esci", "exit", "quit"):
            invia_messaggio_chat(comando)
            continue

        if comando in ("esci", "exit", "quit"):
            console.print("[cyan]A dopo, Lore. 👋[/]")
            break
        elif comando == "chiedi start":
            avvia_chat()
        elif comando == "chiedi stop":
            ferma_chat()
        elif comando.startswith("chiedi"):
            chiedi_domanda_singola(comando.replace("chiedi", "", 1).strip())
        else:
            capito = esegui_comando(comando)
            if not capito:
                console.print(
                    "[red]Non ho capito. Scrivi 'aiuto' per la lista comandi, "
                    "oppure 'chiedi <domanda>' per farmi una domanda vera.[/]"
                )


if __name__ == "__main__":
    main()
