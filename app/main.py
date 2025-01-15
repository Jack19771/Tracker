from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from typing import List
from datetime import datetime, timedelta
from apscheduler.schedulers.background import BackgroundScheduler
from apscheduler.events import EVENT_JOB_EXECUTED, EVENT_JOB_ERROR

app = FastAPI()

# Słownik przechowujący dane o peerach dla każdego pliku
peers = {}

# Model danych dla ogłoszenia peera
class PeerData(BaseModel):
    file_id: str
    peer_info: dict  # Przykład: {"ip": "127.0.0.1", "port": 8080}
    last_announce: datetime

# Model danych dla usunięcia peera
class PeerRemoveData(BaseModel):
    file_id: str
    peer_info: dict

# Model danych dla heartbeata
class HeartbeatData(BaseModel):
    file_id: str
    peer_info: dict

# Funkcja czyszcząca nieaktywnych peerów
def clean_inactive_peers(file_id: str, timeout: timedelta):
    current_time = datetime.now()
    if file_id in peers:
        # Usuwamy peerów, którzy nie ogłaszali się przez określony czas
        active_peers = [
            peer for peer in peers[file_id] 
            if current_time - peer["last_announce"] < timeout
        ]
        peers[file_id] = active_peers

# Inicjalizacja scheduler'a
scheduler = BackgroundScheduler()

# Dodanie zadania do scheduler'a, które będzie uruchamiane co 10 minut
scheduler.add_job(lambda: clean_inactive_peers("all", timedelta(minutes=10)), 'interval', minutes=10)

# Start scheduler'a
scheduler.start()

# Endpoint do ogłaszania nowego peera
@app.post("/announce")
async def announce(peer_data: PeerData):
    file_id = peer_data.file_id
    peer_info = peer_data.peer_info
    last_announce = datetime.now()

    # Zaktualizowanie lub dodanie nowego peera
    if file_id not in peers:
        peers[file_id] = []
    
    # Sprawdzamy, czy peer już istnieje
    existing_peer = next((p for p in peers[file_id] if p["peer_info"] == peer_info), None)
    if existing_peer:
        # Jeśli peer już istnieje, zaktualizujmy czas ogłoszenia
        existing_peer["last_announce"] = last_announce
    else:
        # Jeśli to nowy peer, dodajemy go do listy
        peers[file_id].append({"peer_info": peer_info, "last_announce": last_announce})

    return {"message": "Peer added/updated successfully", "peers": peers[file_id]}

# Endpoint do usunięcia peera
@app.post("/remove_peer")
async def remove_peer(peer_remove_data: PeerRemoveData):
    file_id = peer_remove_data.file_id
    peer_info = peer_remove_data.peer_info

    # Sprawdzamy, czy plik istnieje i czy peer jest na liście
    if file_id in peers:
        peers[file_id] = [peer for peer in peers[file_id] if peer["peer_info"] != peer_info]
    
    return {"message": "Peer removed successfully", "peers": peers.get(file_id, [])}

# Endpoint do uzyskania listy peerów dla danego pliku
@app.get("/peers/{file_id}")
async def get_peers(file_id: str):
    file_peers = peers.get(file_id, [])
    return {"file_id": file_id, "peers": file_peers}

# Endpoint do uzyskania listy wszystkich peerów
@app.get("/peers")
async def get_all_peers():
    all_peers = {file_id: peers[file_id] for file_id in peers}
    return {"peers": all_peers}

# Endpoint do heartbeata (zgłoszenie aktywności peera)
@app.post("/heartbeat")
async def heartbeat(heartbeat_data: HeartbeatData):
    file_id = heartbeat_data.file_id
    peer_info = heartbeat_data.peer_info
    last_announce = datetime.now()

    # Jeśli plik istnieje, sprawdzamy, czy peer jest już na liście
    if file_id in peers:
        existing_peer = next((p for p in peers[file_id] if p["peer_info"] == peer_info), None)
        if existing_peer:
            # Aktualizujemy czas ogłoszenia peera
            existing_peer["last_announce"] = last_announce
        else:
            # Jeśli peer nie istnieje, dodajemy go do listy
            peers[file_id].append({"peer_info": peer_info, "last_announce": last_announce})
    else:
        # Jeśli plik nie istnieje, tworzymy nową listę peerów
        peers[file_id] = [{"peer_info": peer_info, "last_announce": last_announce}]

    return {"message": "Peer heartbeat updated", "peers": peers[file_id]}

# Zatrzymywanie scheduler'a przy zamknięciu aplikacji
@app.on_event("shutdown")
def shutdown():
    scheduler.shutdown()

# Główna strona
@app.get("/")
def read_root():
    return {"message": "Tracker is running"}
