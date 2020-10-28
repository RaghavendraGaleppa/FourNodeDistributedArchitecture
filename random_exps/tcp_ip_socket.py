import socket
import sys

s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)

HOST = sys.argv[-1] if len(sys.argv) == 3 else '127.0.0.1'
PORT =1066

def recv_all(sock, length):
	data = ''
	while(len(data) < length):
		more = sock.recv(length - len(data)).decode()
		if not more:
			raise EOFError(f'Socket closed {len(data)}')
		data += more
	return data

if sys.argv[1] == 'server':
	s.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
	s.bind((HOST, PORT))
	s.listen(1)
	while(True):
		print(f"Listening at: {s.getsockname()}")
		sc, sockname = s.accept()
		print(f"Accepted connection from: {sockname}")
		print(f"Connected {s.getsockname()} and {sc.getpeername()}")
		message = recv_all(sc, 16)
		print(f"The message is: {message}")
		sc.sendall("Farewell, client".encode())
		sc.close()
		print(f"Reply send socket closed")

elif sys.argv[1] == 'client':
	s.connect((HOST, PORT))
	print(f"Client has been assigned socketname: {s.getsockname()}")
	s.sendall("Hello there ma boi".encode())
	reply = recv_all(s, 16)
	print(f"The server said: {reply}")
	s.close()
