from node import Node

def test_f():
	print("Started testing")
	a = Node._build_and_run(port=1060)

	b = Node._build_and_run(port=1061)

	b.upload_payload('asdasdabsfaksjdas')
	a.querry_payload(b.payload_sent[-1])

	b.connect_to_node('127.0.0.1',1060)

	a.kill()
	b.kill()

