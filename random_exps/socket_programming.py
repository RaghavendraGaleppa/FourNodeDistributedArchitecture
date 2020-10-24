import socket, sys

s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)

MAX = 65535 # 64K ports
PORT = int(sys.argv[2]) # Unique to each socket object

if sys.argv[1] == 'server':
	s.bind(('127.0.0.1', PORT))
	print("Listening at: ", s.getsockname())
	while True:
		data, address = s.recvfrom(MAX)
		print(f"The client at {address} says {repr(data)}")
		s.sendto(f"Your data was {len(data)} bytes".encode(), address)


if sys.argv[1] == 'client':
	SEND_PORT = int(sys.argv[3])
	print(f"Address before sending: {s.getsockname()}")
	s.sendto(f"Hello WOrld".encode(),('127.0.0.1',SEND_PORT))
	print(f"Address after sending: {s.getsockname()}")
	data, address = s.recvfrom(MAX)
	print(f"The server {address} says {repr(data)}")
