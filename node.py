import socket
import threading
import time # for sleep function
from datetime import datetime # for creating timestamp as datetime

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
		self.connected_peers = []

	def printh(self, message):
		print(f"({self.hostname}): {message}")

	def run(self):
		"""
			- This is the main function that will be executed on a thread.
			- Waits for data to come and accepts the id of the node
			- At the same time, sends its own id to the target node
			- Creates a P2P channel with the target node
		"""

		try:
			client_sock, client_addr = self.sock.accept()
			client_node_id = client_sock.recv(4096).decode()
			client_sock.sendall(self.id.encode())
			self.printh(f"IDs exchanged with: {client_addr}")

			p2pchannel = P2PChannel(self, client_sock, client_node_id, *client_addr)
			self.connected_peers.append(p2pchannel)
			p2pchannel.start()

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
			self.connected_peers.append(p2pchannel)
			p2pchannel.send_data("Hola")

		except Exception as e:
			self.printh(e)


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
		self.printh(f"Message Recieved from {self.target_id}: {data}")
		
	def send_data(self,message):

		message_ = message.encode() + self.end_byte
		self.target_sock.sendall(message_)
		self.printh(f"Message sent to {self.target_id}: {message}")
