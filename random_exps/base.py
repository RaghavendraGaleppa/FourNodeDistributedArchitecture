import threading
import socket
HOST = '127.0.0.1'
PORT = 1060


def create_socket():
	sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
	sock.setsockopt(SOCK.SOL_SOCKET, socket.SO_REUSEADDR, 1)
	sock.bind((HOST, PORT))
	sock.listen(100)
	return sock

def recv_msg(sock):
	data = b""
	msg = ""
	while not msg:
		more = sock.recv(4096)
		if not more:
			raise EOFError("Socket is not recieving anymore data")

		data += more
		if b'\0' in more:
			msg = data.rstrip(b'\0')

	return msg.decode()
	
		

def send_message(sock, message):
	message.append('\0')
	sock.sendall(message.encode())


