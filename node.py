import socket
import threading
import time # for sleep function
from datetime import datetime # for creating timestamp as datetime
import requests
import json

class Node(threading.Thread):
	"""
		- This class represents a peer. 
		- A peer is an instance of Node, capable of accepting connections from other peers.
		- Send and recieve messages from other peers, and also broadcast a single message to all the 
		other peers that are currently connected to it.
		
		NOTE:
		- At a time, a peer can accept data from only a single other peer, even though this peer maybe be connected 
		to many other peers.

		- If a peer wants to send data to another peer, it must first establish a connection to that peer and that connection
		must be accepted at the target peer, only then the process of sending data can be started.

		- Each peer will have a unique ID that will be created as soon as the Node is instantiated.
		 
		- Peer 2 peer communication will start with first exchanging each other's ID's
	"""

	def __init__(self, host, port):
		"""
			host(str): The host from which the socket can accept connections from.
			port(int): The port to which it can listen to or send to.
		"""
		super(Node,self).__init__() # Initialize the Thread class

		self.host = host
		self.port = port
		self.hostname = (self.host, self.port)

		""" Setup the Socket """
		self.sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
		self.sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
		self.sock.bind(self.hostname)
		self.sock.listen(10)

		""" Initialized Id """
		self.id = datetime.strftime(datetime.now(), "%y%m%d_%H%M%S%f")
		self.printh(f"Created a peer with ID: {self.id}")

		""" Connected Nodes is represented by a P2PCommunication instance initiated with that node """
		""" Key is peer id and value is the p2p object """
		self.connected_peers = {}
		self.live_channel = None # The channel through which the peer is currently communicating through

		""" Each peer needs to ping the trusted server and get a list of other peers that are in contact with the server """
		""" peer_list is dictionary with a key and value pair representing id and hostname respectively for the peer """
		""" This peer_list will be updated every time the peer requests the server for a peer_list """   
		self.peer_list = {}
		

		""" Keep track of all the payloads that have been sent to the server """
		self.payload_sent = []
		self.available_payloads = {}

		self.tracker = None

	def printh(self, message):
		print(f"({self.hostname}): {message}")

	def run(self):
		"""
			- This is the main function that will be executed on a thread.
			- Waits for data to come and accepts the id of the node
			- At the same time, sends its own id to the target node
			- Creates a P2P channel with the target node
		"""

		while True:
			try:
				client_sock, client_addr = self.sock.accept()
				client_node_id = client_sock.recv(4096).decode()
				client_sock.sendall(self.id.encode())
				self.printh(f"IDs exchanged with: {client_addr}")

				p2pchannel = P2PChannel(self, client_sock, client_node_id, *client_addr)
				self.connected_peers[client_node_id] = p2pchannel
				p2pchannel.start()
				p2pchannel.join()

			except socket.timeout:
				self.printh(f"Connection timeout")

			pass

	def connect_to_node(self, host, port):
		"""
			- This function is reponsible for establishing a connection with a seperate node.
		"""
		
		try:
			sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
			sock.connect((host,port))
			sock.sendall(self.id.encode())

			target_node_id = sock.recv(4096).decode()
			self.printh(f"IDs exchanged with: {(host,port)}")

			p2pchannel = P2PChannel(self, sock, target_node_id, host, port)
			self.connected_peers[target_node_id] = p2pchannel
			self.live_channel = p2pchannel

		except Exception as e:
			self.printh(e)

	def register_peer(self, api):
		"""
			- This function will register itself with the trusted server or the tracker

			args:
				api: str - this is the address to the api,
				for example: http://127.0.0.1:8000/,
							http://11.3.7.5,

		"""
		message = {}
		message['peer_id'] = self.id
		message['hostaddr'] = self.host
		message['port'] = self.port
		if api[-1] == '/':
			api = api[:-1]
		r = requests.post(f'{api}/register', json=message)
		if (r.status_code == 200):
			self.tracker = api
			self.printh(r.text)

	def deregister_peer(self):
		"""
			- This function can be used in a way to tell that a peer is being deregistered right before
			shutting down
		"""
		if self.tracker is None:
			raise Exception(f"No tracker is registered yet")

		message = {"peer_id": self.id, 'hostaddr': self.host, 'port': str(self.port)}
		r = requests.delete(f"{self.tracker}/deregister", json=message)
		if r.status_code == 200:
			self.printh(r.text)


	def upload_payload(self, payload_string: str, desc:str =None):
		"""
			- This function is responsible for uploading the payload to the server
		"""
		if self.tracker is None:
			raise Exception(f"No tracker is registered yet")
		
		message = {'payload':payload_string}
		if desc is not None:
			message['desc'] = desc

		r = requests.post(f'{self.tracker}/upload_payload', json=message)
		if r.status_code != 200:
			raise Exception(f"There was an error while sending the payload string")
		else:
			self.printh(f"Successfully upload payload")
			self.printh(f"PayloadId: {r.json()['payloadId']}")

		if r.json()['payloadId'] not in self.payload_sent:
			self.payload_sent.append(r.json()['payloadId'])
			self.available_payloads[r.json()['payloadId']] = payload_string

	def get_peers(self):
		"""
			- This function will return querry the tracker and return a list of all connected peers
		"""
		if self.tracker is None:
			raise Exception(f"No tracker is registered yet")
		r = requests.get(f"{self.tracker}/get_peers")
		return r.json()

	def querry_payload(self, payloadId):
		"""
			- Create a post request with payloadId as data and get back the hashed chunks along with
			full chunks
		"""
		if self.tracker is None:
			raise Exception(f"No tracker is registered yet")
		
		message = {'id': payloadId}
		r = requests.post(f"{self.tracker}/get_payload", json=message)
		if r.status_code != 200:
			raise Exception("There was an error at the server. The request was unsuccessfull")
		else:
			self.printh(f"Successfully Querry of {payloadId} to the server")
		response_data = r.json()
		self.available_payloads[payloadId] = response_data['claimedString']
		return response_data

	def verify_payload(self, payloadId, positions:list = None):
		"""
			- This function initiate the communication between the nodes for the payload verification.

			- positions represents the position of each chunk in the data. Leave it to None if you dont 
			want to jumble up the position of chunks.

			- example: positions = [1,0,3] will say that chunk 0 is at position 1, chunk 1 is at position 0 
			and chunk 2 is at position 3
		"""
	
		if payloadId not in self.available_payloads.keys():
			raise Exception(f"Invalid Payload")
		chunks = []
		for i in range(0, len(self.available_payloads[payloadId]), 4):
			chunks.append(self.available_payloads[payloadId][i:i+4])
		
		message = {}
		message['claims'] = []
		message['payloadId'] = f"{payloadId}"
		if positions == None:
			for i, chunk in enumerate(chunks):
				message['claims'].append({'chunk':chunk, 'position': i})
		else:
			if len(positions) <= len(chunks):
				for i, p in enumerate(positions):
					message['claims'].append({'chunk':chunks[i], 'position': p})
			else:
				raise Exception(f"The lenght of list positions is larger than that of the chunks")

		self.live_channel.send_data(json.dumps(message))

	def parse_claims(self, data):
		"""
			- Get the payloadId and then retrieve that payload from the server
			- get the chunked claimedString and then verify the data.
			- return back the 

		"""
		data = json.loads(data)
		payloadId = data['payloadId']
		if payloadId not in self.available_payloads.keys():
			return json.dumps({'chunk_available':False})

		claimedString = self.available_payloads[payloadId]
		chunks = [claimedString[i:i+4] for i in range(0, len(claimedString), 4)]

		message = {}
		message['results'] = []	
		message['chunk_available'] = True
		for claim in data['claims']:
			message['results'].append(claimedString[claim['position']] == claim['chunk'])
		return json.dumps(message)
		
class P2PChannel(threading.Thread):
	"""
		- This class represents a channel through which both the peers will exchanged data with each other.
	"""

	def __init__(self, main_node, target_sock, target_id, main_host, main_port):
		"""
			args:
				main_node - The node that is being connected
				target_sock - The socket object of target node
				target_id - The id of the target node
				main_host - hostname of the main node
				main_port - the port of the main node
		"""
		
		super(P2PChannel, self).__init__()

		self.main_node = main_node
		self.target_sock = target_sock
		self.target_id = target_id
		self.main_host = main_host
		self.main_port = main_port

		self.printh(f"Started P2P channel with node: {self.target_sock.getpeername()}")

		self.end_byte = b"EOM\x01"

	def printh(self,message):
		print(f"({self.main_node.hostname})P2P: {message}")


	def run(self):
		"""
			- This is thread loop where the node keeps waiting for the data to come.
			- The message should have a stop byte, which is same for all the nodes.
			- At the moment, this channel is not encrypted. 
		"""
		data = b""
		message = b""
		
		while not data:
			chunk = self.target_sock.recv(4096)
			message += chunk
			if self.end_byte in message:
				data += message.rstrip(self.end_byte)
		
		data = data.decode()
		message = self.main_node.parse_claims(data)		
		self.target_sock.sendall(message.encode() + self.end_byte)
		self.target_sock.close()
		
	def send_data(self,message):

		message_ = message.encode() + self.end_byte
		self.target_sock.sendall(message_)
		self.printh(f"Message sent to {self.target_id}: {message}")
		response = b""
		data = b""
		while not response:
			chunk = self.target_sock.recv(4096)
			data += chunk
			if self.end_byte in data:
				response += data.rstrip(self.end_byte)

		response = response.decode()
		print(json.loads(response))
		self.target_sock.close()


