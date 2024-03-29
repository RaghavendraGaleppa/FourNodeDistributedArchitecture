# PowerloomAssignment
Usage: export PYTHONPATH=src; 
redis-server &;
python3 src/server.py &;
python3 simulate.py;

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

### TODO:
	- [x] Successfully test the api by sending a register post request to the server
	- [x] Send a payload string from a peer and get back the payloadId
	- [x] API calls to register and querry for registered peers
	- [x] Implement the hashing function that is required for the payload load string
	- [x] Implement the payload Querry API and test it.
	- [x] Create interface for a peer to querry with other peer about the chunk position
	- [x] Make the threads daemon
	- [x] A peer cannot accept a connection from other peer while it is in communication a previous peer (Implement using thread.join() call). This will work in convention with p2pchannels thread where the main peer thread will wait for p2pchannels thread to finish.
	- [x] Make sure that each (host,port) combination is not repeated in the server for the list of peers connected to it.
	- [x] Each peer needs to have a deregister function that will erase their entry from the peer list in the server
	- [x] Log all the activities/communications into a log file
	- [x] Use counters for each of the peers to make sure all their activities are measured.
	- [x] Build functions for peers to querry them about their metrics of all the activities.
	- [x] Peer and socket shutdown functions need to be created
	- [x] Write proper simualtion code
	- [X] Pre-deadline last commit: 7385171 (no alphabets in this hash)

	# POST DEADLINE FIXES:
	- [x] Error: pyaloadId missing
	- [x] Reorganize folder into tests and src folder
	- [x] Integrate github actions.
	- [x] Fully integrated and tested all kinds of actions for both peers and server using github actions. If any error comes up after 
	commits, it will be caught.

