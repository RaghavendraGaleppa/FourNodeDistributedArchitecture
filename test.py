from node import Node
import time

node1 = Node('127.0.0.1',1060)
node2 = Node('127.0.0.1',1061)

node1.start()

node2.connect_to_node('127.0.0.1',1060)
