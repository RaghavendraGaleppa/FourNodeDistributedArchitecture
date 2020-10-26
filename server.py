from fastapi import FastAPI, Request
from pydantic import BaseModel
from typing import Optional, List
from datetime import datetime

import redis
import hashlib

app = FastAPI()
conn = redis.StrictRedis(host='localhost', port=6379)

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

def generate_hashes(payload_string):
	"""
		- The string will be split into a list of new strings with 4 characters each
		- Each of those new strings will be hashed
		- Every single hash of the new strings will be added and hashed together to
		create a new hash string which will be returned along with the list of chunks
	"""
	hashes = []
	for i in range(0,len(payload_string), 4):
		hash_ = hashlib.sha224(payload_string[i:i+4].encode()).hexdigest()
		hashes.append(hash_)
	
	full_hash = hashlib.sha224(''.join(hashes).encode()).hexdigest()
	return hashes, full_hash	


def custom_encode(string_par):
	if len(string_par) < 12:
		string_par = string_par + ''.join([str(i) for i in range(12-len(string_par))])
	x = [i for i in range(12)]
	for i in range(len(string_par)):
		x[i % len(x)] = x[i % len(x)] * ord(string_par[i])
		x[i % len(x)] = 65 + x[i % len(x)] % 25
	
	new_x = ''.join([chr(k) for k in x])
	return f"payload_{new_x}"

def get_id(payload_string):
	"""
		- return a unique id for the payload
	"""
	return f'payload_{hash(payload_string)}'


@app.post("/register/")
async def register_peer(peer: Peer, request: Request):
	try:
		if not conn.sismember("list:peers", f"{peer.peer_id}"):
			conn.hset(f"peer:{peer.peer_id}", "hostaddr", f"{peer.hostaddr}")
			conn.hset(f"peer:{peer.peer_id}", "port", f"{peer.port}")
			conn.sadd(f"list:peers", f"{peer.peer_id}")
		else:
			return {"message": "Peer already registered"}
	except Exception as e:
		print(f"{e}")
		return {"message": "Due to an error at the backend, registration was unsuccessfull"}

	return {"message": "Successfully Registered"}

@app.post("/upload_payload/")
async def upload_payload(str_payload: StringPayload):
	"""
		- Accept a payload string, hash it and return its payload Id

		- Check if the payload already exists in the database, if so then just return the payload Id. 
		Check the set list:payloads for the list of payloads that have been uploaded to the trusted server.

		- if the payload is not already present, then generate hash_chunks and full_hash for the payload.

		- insert the chunked hashes into the chunks:payloadId hash. It is important to keep the order of the
		chunks that occur in the payload string.

		- Insert the full_hash, claimed string and chunksid into the hash:payloadId hash

	"""
	payloadId = custom_encode(str_payload.payload)
	if conn.sismember('list:payloads', payloadId):
		return {'payloadId':payloadId}

	# Save the data as hashes
	hash_chunks, full_hash = generate_hashes(str_payload.payload)
	for i, h in enumerate(hash_chunks):
		conn.hset(f'chunks:{payloadId}', f'{i}', h)
	
	conn.hset(f'hash:{payloadId}', 'rootHash', full_hash)
	conn.hset(f'hash:{payloadId}', 'claimedString', str_payload.payload)
	conn.hset(f'hash:{payloadId}', 'chunks', f'chunks:{payloadId}')

	conn.sadd('list:payloads', payloadId)
	return {'payloadId':payloadId}

@app.get("/get_peers/")
async def get_peers():
	connected_peers = conn.smembers('list:peers')
	data = {}
	for peer in connected_peers:
		data[peer.decode()] = conn.hgetall(f"peer:{peer.decode()}")
	return data

