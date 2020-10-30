from fastapi import FastAPI, Request
from pydantic import BaseModel
from typing import Optional, List
from datetime import datetime

import redis
import hashlib
import uvicorn
import logging

logger = logging.getLogger(__name__)
logger.addHandler(logging.NullHandler())
app = FastAPI()
app.logger = logger
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

	def __str__(self):
		return ', '.join([self.peer_id, self.hostaddr, self.port])

	def __repr__(self):
		return ', '.join([self.peer_id, self.hostaddr, self.port])

class PayloadId(BaseModel):
	id: str

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
			peers_connected = conn.keys("peer:*")
			for single_peer in peers_connected:
				data = conn.hgetall(f"{single_peer.decode()}")
				if data[b'hostaddr'].decode() == peer.hostaddr and data[b'port'].decode() == peer.port:
					conn.delete(single_peer)
					conn.srem("list:peers",single_peer.decode().split(':')[-1])
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

@app.post("/get_payload/")
async def get_payload(payload_id: PayloadId):

	if not conn.sismember('list:payloads',payload_id.id):
		return {'valid_payload': False}
		
	chunks = conn.hgetall(f'chunks:{payload_id.id}')
	message = {"chunks": []}
	for key, value in chunks.items():
		message["chunks"].append(value.decode())

	message["rootHash"] = conn.hget(f'hash:{payload_id.id}', 'rootHash').decode()
	message["claimedString"] = conn.hget(f'hash:{payload_id.id}', 'claimedString').decode()
	
	return message

@app.get("/get_peers/")
async def get_peers():
	connected_peers = conn.smembers('list:peers')
	print(connected_peers)
	data = {}
	for peer in connected_peers:
		data[peer.decode()] = conn.hgetall(f"peer:{peer.decode()}")
	return data

@app.delete("/deregister")
async def deregister_peer(peer: Peer):
	"""
		- Check if the peer is there in the list of connected peers
		- if so, then check for the host addr and port verification 
		- if true then delete its entry from list of peers and also delete the peers hash
	"""
	connected_peers = conn.smembers('list:peers')
	if f"{peer.peer_id}".encode() in connected_peers:
		data = conn.hgetall(f"peer:{peer.peer_id}")
		if data[b'hostaddr'].decode() == peer.hostaddr and data[b'port'].decode() == peer.port:
			conn.delete('peer:{peer.peer_id}')
			conn.srem('list:peers', f'{peer.peer_id}')
			return {"message": f"The Peer {peer.peer_id} has been successfully deregistered"}
	else:
		return {"message": "Peer not found"}
	
