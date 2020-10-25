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
		print(f"Created a peer with ID: {self.id}")

		""" Connected Nodes is represented by a P2PCommunication instance initiated with that node """
		self.connected_peers = []

	def run(self):
		"""
			- This is the main function that will be executed on a thread.
			- Waits for data to come and accepts the id of the node
		"""

		try:
			client_sock, client_addr = self.sock.accept()
			client_node_id = client_sock.recv(4096).decode()
			client_sock.sendall(self.id.encode())
			print(f"IDs exchanged with: {client_addr}")

		except socket.timeout:
			print(f"Connection timeout")

		pass

	def connect_to_node(self, host, port):
		"""
			- This function is reponsible for establishing a connection with a seperate node.
		"""
		
		try:
			sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
			sock.connect((host,port))
			sock.sendall(self.id.encode())

			target_node_id = sock.recv(4096)
			print(f"IDs exchanged with: {(host,port)}")

		except Exception as e:
			print(e)
		
