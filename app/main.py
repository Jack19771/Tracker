from fastapi import FastAPI
from pydantic import BaseModel
from typing import List
from datetime import datetime, timedelta
from apscheduler.schedulers.background import BackgroundScheduler
import logging

# Ustawienie logowania
logging.basicConfig(level=logging.INFO)

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

# Funkcja czyszcząca nieaktywnych peerów
def clean_inactive_peers():
    current_time = datetime.now()
    logging.info(f"Running clean_inactive_peers at {current_time}")
    
    for file_id in list(peers.keys()):
        print(f"Cleaning peers for file_id: {file_id}, current time: {current_time}")
        logging.info(f"Cleaning peers for file_id: {file_id}, current time: {current_time}")
        
        # Usuwamy peerów, którzy nie ogłaszali się przez określony czas
        active_peers = [
            peer for peer in peers[file_id] 
            if current_time - peer["last_announce"] < timedelta(minutes=1)
        ]
        
        # Logowanie usuwania
        removed_peers = len(peers[file_id]) - len(active_peers)
        if removed_peers > 0:
            print(f"Removed {removed_peers} inactive peers for file {file_id}")
            logging.info(f"Removed {removed_peers} inactive peers for file {file_id}")
        
        # Jeśli nie usunięto peerów, logujemy, że nikt nie został usunięty
        if removed_peers == 0:
            print(f"No peers removed for file {file_id}. All peers are active.")
            logging.info(f"No peers removed for file {file_id}. All peers are active.")
        
        peers[file_id] = active_peers

# Ustawienie scheduler'a do uruchamiania czyszczenia co 10 minut
scheduler = BackgroundScheduler()
scheduler.add_job(clean_inactive_peers, 'interval', minutes=1)
scheduler.start()

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

    # Logowanie dodania/aktualizacji peera
    print(f"Peer {peer_info} added/updated for file {file_id}, last_announce: {last_announce}")
    logging.info(f"Peer {peer_info} added/updated for file {file_id}, last_announce: {last_announce}")

    return {"message": "Peer added/updated successfully", "peers": peers[file_id]}

@app.post("/remove_peer")
async def remove_peer(peer_remove_data: PeerRemoveData):
    file_id = peer_remove_data.file_id
    peer_info = peer_remove_data.peer_info

    # Sprawdzamy, czy plik istnieje i czy peer jest na liście
    if file_id in peers:
        peers[file_id] = [peer for peer in peers[file_id] if peer["peer_info"] != peer_info]
    
    print(f"Peer {peer_info} removed from file {file_id}")
    logging.info(f"Peer {peer_info} removed from file {file_id}")

    return {"message": "Peer removed successfully", "peers": peers.get(file_id, [])}

@app.get("/peers/{file_id}")
async def get_peers(file_id: str):
    """
    Pobiera listę peerów dla danego pliku.
    """
    file_peers = peers.get(file_id, [])
    return {"file_id": file_id, "peers": file_peers}
