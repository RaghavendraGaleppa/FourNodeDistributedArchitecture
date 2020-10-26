from fastapi import FastAPI
from pydantic import BaseModel
from typing import Optional


class StringPayload(BaseModel):
	payload: str
	desc: Optional[str] = None

class Peer(BaseModel):
	peer_id: str
	hostaddr: str
	port: str

app = FastAPI()

@app.post("/register/")
async def register_peer(peer: Peer):
	print(Peer)
	return {"message": "Successfully Registered"}

@app.get("/")
async def upload_payload():
	# Save the payload onto the database and return the payload_id
		
	return {'message':'heya'}
