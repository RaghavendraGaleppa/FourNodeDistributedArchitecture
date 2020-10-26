# PowerloomAssignment

- Peer (Node):
	- A Peer is a unanimous node, which is independently in itself both client and server.
	- A Peer does not need to be dependent some central system to function.
	- For now I will implement peer node's as just sockets which are bound to different ports on the 
	same machine.

- Implementation of a Node:
	- Each peer is represented by a class Node. This class will have a socket which will be binded to 
	the local host with a unique port number.
	- A socket bind represents that the peer is ready to accept connections (tcp handshake) at that port.
	- A socket connect represents that the peer is ready to initiate the tcp handshake with the target peer.

- Trusted Server (Tracker):
	- The trusted server is an api through which each peer can querry it for different types of information.
	- Peers can upload a payload string to the server through the API, and the server returns a payloadId back 
	to the peer which is unique to that string

	- Each peer reports itself to the server, and the server maintains a list of all the peers that have reported to it.

