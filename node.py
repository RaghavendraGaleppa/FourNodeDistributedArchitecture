import socket
import threading
import time # for sleep function
from datetime import datetime # for creating timestamp as datetime
import requests
import json

from enum import Enum
import redis

class SEVERITY(Enum):

	# Activities/Communication with other peers
	KILL = 7
	PEER_INTIALIZED = 8
	SHUTDOWN_SOCK = 9
	VERIFY_CLAIM = 10
	PARSE_CLAIM = 13
	CONNECT_TO_NODE = 15

	# Activities/Communication with the trusted server
	UPLOAD_PAYLOAD = 20
	QUERRY_PAYLOAD = 23
	REGISTER_PEER = 25
	DEREGISTER_PEER = 30
	GET_PEERS = 33


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
		#self.sock.settimeout(0.2)
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
		self.stop_thread = 0
		self._stop_event = threading.Event()

		""" 
			- Each peer will have different modes of severity which will be used for logging their data 
			and keeping track of its activities/communications. Along with that each peer will get multiple 
			counters for every activity that takes place. These counters will be saved in Redis and can be later 
			querried. 
		"""
		self.conn = redis.StrictRedis()
		self.trim = 100 # This will tell how many recent logs to keep. Set it as None to so that all logs will be kept
		log_message = f"Peer initialized with id: {self.id}, listening at {self.hostname}"
		self.log_activities(log_message, SEVERITY.PEER_INTIALIZED)
		
	
	def shutdown(self):
		self.sock.shutdown(socket.SHUT_RD)
		self.sock.close()
		log_message = f"Socket has been shutdown"
		self.log_activities(log_message, SEVERITY.SHUTDOWN_SOCK)

	def printh(self, message):
		print(f"({self.hostname}): {message}")

	def kill(self):
		self.stop_thread = 1
		self.deregister_peer()
		self.shutdown()
		log_message = f"Peer has been killed"
		self.log_activities(log_message, SEVERITY.KILL)

	def log_activities(self, message, severity_level):
		"""
			- A Peer can log activities based on whether they are commiunicating with the trusted server or 
			another peer.

			- All activities/communications with another peer will be saved into a Redis List with the key: 
			p2p:host:port.peer_id:SEVERITY_LEVEL

			- All activities/communications with the trusted server will be saved into a Redis List with key:
			http:host:port.peer_id:SEVERITY_LEVEL

			- Along with these lists, each peer with have its own counters for every severity level with key:
			counter:host:port.peer_id:SEVERITY_LEVEL

		"""

		# Check if that severity_level exists
		if isinstance(severity_level, SEVERITY):
			severity_level = severity_level.value
		try:
			SEVERITY(severity_level)

		except ValueError as e:
			self.printh(f"The severity level {severity_level} does not exist. The message will not be logged")

		
		postfix = f"{self.host}:{self.port}.{self.id}:{SEVERITY(severity_level).name}"
		counter_dest = f"counter:{postfix}"
		destination = ""
		if severity_level <= SEVERITY.CONNECT_TO_NODE.value:
			destination = f"p2p:{postfix}"
		else:
			destination = f"http:{postfix}"
		pipe = self.conn.pipeline()

		# Log the message
		timestamp = datetime.strftime(datetime.now(), "%y/%m/%d %H:%M:%S")
		message = timestamp + message
		pipe.lpush(destination, message)
		if self.trim and isinstance(self.trim, int):
			pipe.ltrim(destination, 0, self.trim)

		# increase counters
		pipe.incr(counter_dest)
		pipe.execute()

	def run(self):
		"""
			- This is the main function that will be executed on a thread.
			- Waits for data to come and accepts the id of the node
			- At the same time, sends its own id to the target node
			- Creates a P2P channel with the target node
		"""

		while True:
			if self.stop_thread:
				print("Thread Stopped")
				self._stop_event.set()
				break
			try:
				client_sock, client_addr = self.sock.accept()
				client_node_id = client_sock.recv(4096).decode()
				client_sock.sendall(self.id.encode())
				self.printh(f"IDs exchanged with: {client_addr}")

				p2pchannel = P2PChannel(self, client_sock, client_node_id, *client_addr)
				self.connected_peers[client_node_id] = p2pchannel
				self.live_channel = p2pchannel
				self.live_channel.start()
				self.live_channel.join()

			except socket.timeout:
				self.printh(f"Connection timeout")
			except OSError:
				self.printh(f"The socket has been shutdown")


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
			self.live_channel.start()
			log_message = f"Connected to node: {(host, port)} with id: {target_node_id}"
			self.log_activities(log_message, SEVERITY.CONNECT_TO_NODE.value)

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
			log_message = f"Registered to tracker(trusted server): {self.tracker}"
			self.log_activities(log_message, SEVERITY.REGISTER_PEER.value)

	def deregister_peer(self):
		"""
			- This function can be used in a way to tell that a peer is being deregistered right before
			shutting down
		"""
		if self.tracker is None:
			self.printh(f"The peer is not registered with any tracker")

		message = {"peer_id": self.id, 'hostaddr': self.host, 'port': str(self.port)}
		r = requests.delete(f"{self.tracker}/deregister", json=message)
		if r.status_code == 200:
			self.printh(r.text)
			log_message = f"De-Registered with tracker(trusted server): {self.tracker}"
			self.tracker = None
			self.log_activities(log_message, SEVERITY.DEREGISTER_PEER.value)


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
			log_message = f"Uploaded payload: {r.json()['payloadId']} to server: {self.tracker}"
			self.log_activities(log_message, SEVERITY.UPLOAD_PAYLOAD)

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
		log_message = f"Got the list of peers from server: {self.tracker}"
		self.log_activities(log_message, SEVERITY.GET_PEERS)
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
			log_message = f"Got chunk hashes for {payloadId} from server {self.tracker}"
			self.log_activities(log_message, SEVERITY.QUERRY_PAYLOAD)
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

		log_message = f"Sending data to {self.live_channel.target_sock.getpeername()} ({self.live_channel.target_id}) to verify data"	
		self.log_activities(log_message, SEVERITY.VERIFY_CLAIM)
		data = self.live_channel.send_data(json.dumps(message))
		return data

	def parse_claims(self, data):
		"""
			- Get the payloadId and then retrieve that payload from the server
			- get the chunked claimedString and then verify the data.
			- return back the 

		"""
		data = json.loads(data)
		if 'payloadId' not in data.keys():
			return 'Corrupted Data recieved: ' + json.dumps(data)
		payloadId = data['payloadId']
		if payloadId not in self.available_payloads.keys():
			return json.dumps({'chunk_available':False})

		claimedString = self.available_payloads[payloadId]
		chunks = [claimedString[i:i+4] for i in range(0, len(claimedString), 4)]
		#print(self.available_payloads[payloadId])
		#print(data)

		message = {}
		message['results'] = []	
		message['chunk_available'] = True
		for claim in data['claims']:
			message['results'].append(chunks[claim['position']] == claim['chunk'])

		log_message = f"Parsing data recieved from {self.live_channel.target_sock.getpeername()} ({self.live_channel.target_id})"	
		self.log_activities(log_message, SEVERITY.PARSE_CLAIM)
		return json.dumps(message)

	def metrics(self, metric_type=None, ignore_id=False):
		"""
			- Get the metrics of the peer
			- metric_type will correspond to the SEVERITY of each log
			- you can either get metrics of peer of current id or get all the metrics of peer by the current hostname of all id's
		"""

		data = {}
		if metric_type is None:
			metric_type = list(SEVERITY)
		else:
			if not isinstance(metric_type, list):
				metric_type = [metric_type]

		for severity in metric_type:
			name = ""
			if isinstance(severity, SEVERITY):
				name = severity.name

			elif isinstance(severity, int):
				name = SEVERITY(severity).name

			else:
				raise ValueError("Invalid metric_type, it can either be int, list or instance of SEVERITY")

			data[name] = []
			prefix = f"counter:{self.host}:{self.port}"
			if ignore_id:
				prefix = f"{prefix}.*:{name}"
			else:
				prefix = f"{prefix}.{self.id}:{name}"

			keys = self.conn.keys(prefix)
			for k in keys:
				data[name].append(int(self.conn.get(k).decode()))

			for k in data.keys():
				try:
						data[k] = sum(data[k])
				except:
					pass

		return data
		
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
			chunk = self.target_sock.recv(10000)
			message += chunk
			if self.end_byte in message:
				data += message.rstrip(self.end_byte)
		
		data = data.decode()
		message = self.main_node.parse_claims(data)		
		self.target_sock.sendall(message.encode() + self.end_byte)
		
	def send_data(self,message):

		message_ = message.encode() + self.end_byte
		self.target_sock.sendall(message_)
		self.printh(f"Message sent to {self.target_id}")
		response = b""
		data = b""
		while not response:
			chunk = self.target_sock.recv(4096)
			data += chunk
			if self.end_byte in data:
				response += data.rstrip(self.end_byte)

		response = response.decode()
		#self.target_sock.close()
		data = json.loads(response)
		return data


