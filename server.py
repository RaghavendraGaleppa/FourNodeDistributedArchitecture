from fastapi import FastAPI
from pydantic import BaseModel
from typing import Optional, List
from datetime import datetime

app = FastAPI()

class StringPayload(BaseModel):
	payload: str
	desc: Optional[str] = None

class StringHashPayload(BaseModel):
	claimedString: str
	rootHash: str
	chunks: List[str]

class Peer(BaseModel):
	peer_id: str
	hostaddr: str
	port: str

def hasing_function(payload_string):
	"""
		- The string will be split into a list of new strings with 4 characters each
		- Each of those new strings will be hashed
		- Every single hash of the new strings will be added and hashed together to
		create a new hash string which will be returned along with the list of chunks
	"""

	pass


def custom_encode(string_par):
	x = [i for i in range(12)]
	for i in range(len(string_par)):
		x[i % len(x)] = x[i % len(x)] * ord(string_par[i])
		x[i % len(x)] = 65 + x[i % len(x)] % 25
		print(x)
	
	new_x = ''.join([chr(k) for k in x])
	return f"payload_{new_x}"

def get_id(payload_string):
	"""
		- return a unique id for the payload
	"""
	return f'payload_{hash(payload_string)}'


@app.post("/register/")
async def register_peer(peer: Peer):
	print(Peer)
	return {"message": "Successfully Registered"}

@app.post("/upload_payload/")
async def upload_payload(str_payload: StringPayload):
	"""
		Accept a payload string, hash it and return its payload Id
	"""
	payloadId = custom_encode(str_payload.payload)
	return payloadId

