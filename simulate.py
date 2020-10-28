import node
from node import SEVERITY
from node import Node
import time
import random
import string

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

unused_port_num = 1064

actions = node.SEVERITY
actions_list = list(node.SEVERITY)

active_peers = [node_1, node_2, node_3, node_4]

vocabulary = string.printable
def generate_random_payload():
	textlen = random.choice(range(100,500))

	# generate random strings
	payload_l = [random.choice(vocabulary) for i in range(textlen)]
	payload = ''.join(payload_l)
	return payload

while True: 
	if len(active_peers) < 2:
		print(f"Not enough peers. creating one")
		node_temp = Node('127.0.0.1',unused_port_num)
		node_temp.daemon = True
		node_temp.start()
		node_temp.register_peer('http://127.0.0.1:8000')
		unused_port_num += 1
		active_peers.append(node_temp)
		time.sleep(2)
		print("="*80)
		print()
		continue

	action = random.choice(actions_list)
	if action == SEVERITY.KILL:
		node_a = active_peers.pop()
		node_a.kill()
		print(f"Killing the node: node_a.hostname")
		print("="*80)
		print()
		time.sleep(2)

	if action == SEVERITY.VERIFY_CLAIM:
		node_a = active_peers.pop()
		node_b = active_peers.pop()

		print(f"Verify Payload")
		
		if len(node_a.available_payloads) == 0:
			node_a.upload_payload(generate_random_payload())
			print(f"No payload exists to verify, uploading a payload")

		payloadId = random.choice(list(node_a.available_payloads.keys()))

		if payloadId not in node_b.available_payloads.keys():
			node_b.querry_payload(payloadId)
		
		print(f"Using payload: {payloadId} for verifying chunks")
		node_a.connect_to_node(node_b.host, node_b.port)
		try:
			if random.choice([0,1]) == 0:
				print(f"Verifying in proper order")
				print(node_a.verify_payload(payloadId))
			else:
				print(f"Verifying in random order")
				positions = len(node_a.available_payloads[payloadId]) // 4
				prefix, postfix = positions[:5], positions[5:]
				random.shuffle(prefix)
				positions = prefix + postfix
				print(node_a.verify_payload(payloadId, positions))
		except:
			print(f"ERROR: WHILE VERIFYING DATA")

		#node_a.live_channel.join()
		
		print("="*80)
		print()
		active_peers.append(node_a)
		active_peers.append(node_b)
		time.sleep(2)

	if action == SEVERITY.GET_PEERS:
		print(f"Get peer list from the sever")
		peer = random.choice(active_peers)
		print(peer.get_peers())
		print("="*80)
		print()
		time.sleep(2)

	if action == SEVERITY.QUERRY_PAYLOAD:
		print(f"Querry a payload and get chunks")
		peer = random.choice(active_peers)
		if len(peer.available_payloads) == 0:
			peer.upload_payload(generate_random_payload())
			print(f"No payload exists to querry, uploading a payload")
		payloadId = list(peer.available_payloads.keys())[0]
		dd = peer.querry_payload(payloadId)
		print(f"claimedString: {dd['claimedString']}")
		print(f"Root Hash: {dd['rootHash']}")
		print("="*80)
		print()
		time.sleep(2)

	if action == SEVERITY.DEREGISTER_PEER:
		print(f"Deregister a peer")
		peer = active_peers.pop()
		peer.deregister_peer()
		print("="*80)
		print()
		time.sleep(2)
