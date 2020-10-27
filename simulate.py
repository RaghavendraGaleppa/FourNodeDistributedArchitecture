import node
import time

print("CREATING PEERS")
print("="*70)
node_1 = node.Node('127.0.0.1', 1060)
node_1.daemon = True
node_1.start()
time.sleep(0.5)
node_2 = node.Node('127.0.0.1', 1061)
node_2.daemon = True
node_2.start()
time.sleep(0.5)
node_3 = node.Node('127.0.0.1', 1062)
node_3.daemon = True
node_3.start()
time.sleep(0.5)
node_4 = node.Node('127.0.0.1', 1063)
node_4.daemon = True
node_4.start()
time.sleep(0.5)

print(" ")
print("="*70)
print("REGISTERING PEERS")
print("="*70)

node_1.register_peer('http://127.0.0.1:8000')
time.sleep(0.5)
node_2.register_peer('http://127.0.0.1:8000')
time.sleep(0.5)
node_3.register_peer('http://127.0.0.1:8000')
time.sleep(0.5)
node_4.register_peer('http://127.0.0.1:8000')
time.sleep(0.5)

print(" ")
print("="*70)
print("QUERRY FOR THE LIST OF REGISTERED PEERS")
print("="*70)

data = node_1.get_peers()
for key in data:
	print(f"{key}: ({data[key]['hostaddr']}, {data[key]['port']})")

print(" ")
print("="*70)
print("UPLOAD PAYLOAD TO THE SERVER")
print("="*70)
node_1.upload_payload("My name is Raghavendra Galeppa")
time.sleep(0.5)

print(" ")
print("="*70)
print(f"QUERRY PAYLOAD {node_1.payload_sent[-1]}")
print("="*70)
node_2.querry_payload(node_1.payload_sent[-1])
time.sleep(0.5)

print(" ")
print("="*70)
print(f" VERIFY PAYLOAD ")
print("="*70)
node_1.connect_to_node('127.0.0.1',1061)
node_1.verify_payload(node_1.payload_sent[-1])
