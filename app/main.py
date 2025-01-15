from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from typing import List, Dict

app = FastAPI()

# Lista peerów dla plików
peers: Dict[str, List[dict]] = {}

# Schemat danych wejściowych
class PeerData(BaseModel):
    file_id: str
    peer_info: dict  # Przykład: {"ip": "127.0.0.1", "port": 8080}

@app.post("/announce")
async def announce(peer_data: PeerData):
    file_id = peer_data.file_id
    peer_info = peer_data.peer_info

    if file_id not in peers:
        peers[file_id] = []
    if peer_info not in peers[file_id]:
        peers[file_id].append(peer_info)

    return {"message": "Peer added successfully", "peers": peers[file_id]}

@app.get("/peers/{file_id}")
async def get_peers(file_id: str):
    file_peers = peers.get(file_id, [])
    return {"file_id": file_id, "peers": file_peers}
