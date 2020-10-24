import threading 
import base

def handle_client(sock, addr):

	try:
		msg = base.recv_msg(sock)
		print(msg)
		base.send_message(sock, '**'+msg+'**')
	except:
		print("SOCKET ERROR")
	finally:
		sock.close()
		print(f"Socket closed")

if __name__ == "__main__":

	server_sock = base.create_socket()
	addr = server_sock.getsockname()
	print(f"Listening on {addr}")

	while True:
		client_sock, addr = server_sock.accept()
		thread = threading.Thread(target=handle_client, args=[client_sock, addr],
								daemon=True)
		thread.start()
		print(f"Connection from {addr}")

