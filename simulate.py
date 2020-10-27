import node
from node import Node
import time

print('='*20 + "Creating Peers" + '='*20)
node_1 = Node('127.0.0.1',1060)
node_1.daemon = True
node_1.start()
node_1.register_peer('http://127.0.0.1:8000')

node_2 = Node('127.0.0.1',1061)
node_2.daemon = True
node_2.start()
node_2.register_peer('http://127.0.0.1:8000')

node_3 = Node('127.0.0.1',1062)
node_3.daemon = True
node_3.start()
node_3.register_peer('http://127.0.0.1:8000')

node_4 = Node('127.0.0.1',1063)
node_4.daemon = True
node_4.start()
node_4.register_peer('http://127.0.0.1:8000')

unused_port_num = 1063

actions = ["register_new_peer", "get_peer", "claim_string_true", "claim_string_false",  "upload_payload",]
#while True:
#
#	if actions == ["
#
node_1.deregister_peer()

