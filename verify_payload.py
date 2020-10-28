from node import Node

a = Node('127.0.0.1',1060)
a.daemon = True
a.start()
a.register_peer('http://127.0.0.1:8000')

b = Node('127.0.0.1',1061)
b.daemon = True
b.start()
b.register_peer('http://127.0.0.1:8000')

b.upload_payload('asdasdabsfaksjdas')
a.querry_payload(b.payload_sent[-1])

b.connect_to_node('127.0.0.1',1060)

print(b.verify_payload(b.payload_sent[-1]))

a.kill()
b.kill()
