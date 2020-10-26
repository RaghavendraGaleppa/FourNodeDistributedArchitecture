import node
import time

print("CREATING PEERS")
print("="*70)
node_1 = node.Node('127.0.0.1', 1060)
time.sleep(0.5)
node_2 = node.Node('127.0.0.1', 1061)
time.sleep(0.5)
node_3 = node.Node('127.0.0.1', 1062)
time.sleep(0.5)
node_4 = node.Node('127.0.0.1', 1063)
time.sleep(0.5)

print("="*70)
print("REGISTERING PEERS")
print("="*70)

node_1.register_peer('http://127.0.0.1:8000')
time.sleep(0.2)
node_2.register_peer('http://127.0.0.1:8000')
time.sleep(0.2)
node_3.register_peer('http://127.0.0.1:8000')
time.sleep(0.2)
node_4.register_peer('http://127.0.0.1:8000')
time.sleep(0.2)

print("="*70)
print("QUERRY FOR THE LIST OF REGISTERED PEERS")
print("="*70)

data = node_1.get_peers()
for key in data:
	print(f"{key}: ({data[key]['hostaddr']}, {data[key]['port']})")
