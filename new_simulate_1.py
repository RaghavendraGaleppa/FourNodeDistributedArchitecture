from node import Node

node = Node('127.0.0.1',1061)
node.daemon = True
node.start()
node.register_peer('http://127.0.0.1:8000')
node.connect_to_node('127.0.0.1',1060)

while True:
	pass
