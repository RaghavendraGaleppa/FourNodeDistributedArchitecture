from node import Node

node = Node('127.0.0.1',1060)
node.daemon = True
node.start()
node.register_peer('http://127.0.0.1:8000')

while True:
	pass
