import xmlrpc.client
import random
import time
from socketserver import ThreadingMixIn
from xmlrpc.server import SimpleXMLRPCServer 
import threading, queue
import string
import logging
from xmlrpc.client import Error
import json
import sys

class Node:
    def __init__(self,host,port):
        self.host = host
        self.port = port
        self.connections = 0

class ServerManager():
    def __init__(self):
        self.nodes = []
        self.supported_methods = ['find_path','attach','detach']
        self.secretstring = 'abbcvfffd32xXx123'


    def run_server(self,host="localhost", port=8000,logRequests=True):
        server_addr = (host, port)
        server = SimpleThreadedXMLRPCServer(server_addr,allow_none=True)
        server.register_function(self.dispatch, 'dispatch')
        server.register_function(self.attach, 'attach')
        server.register_function(self.detach, 'detach')
        server.register_introspection_functions()


        print("Main Node Started")
        print('listening on {} port {}'.format(host, port))

        try:
            print('Control C exits...')
            server.serve_forever()
        except KeyboardInterrupt:
            print('Exiting')
    
    def find_lowest(self):
        lowest = 9999
        found_node = self.nodes[0]
        for node in self.nodes:
            if(node.connections <= lowest):
                lowest = node.connections
                found_node = node
        return found_node


    def resolve_node_command(self,node,node_instance,x,y):
        node_methods = node_instance.system.listMethods()
        for method in self.supported_methods:
            if(method not in node_methods):
                print("VALIDATE ERROR")
                return "VALIDATE ERROR"
            else:
                # self.attach_node(node)

                result = node_instance.find_path(x,y)
                node.connections -= 1
                print(f'Node {node.port} Finished {x,y}, CONNECTIONS:{node.connections}')
                return result

    def dispatch(self,x,y):
        
        while True:
            try:
                node = self.find_lowest()
                node_instance = xmlrpc.client.ServerProxy("http://{}:{}/"
                .format(node.host,node.port))
                node.connections += 1
                print(f'Node {node.port} Working on {x,y}, CONNECTIONS:{node.connections}')
                result = json.dumps(self.resolve_node_command(node,node_instance,x,y))
                return result
            except xmlrpc.client.Error as er:
                print("ERROR", er)
                return er

        

    def attach(self,node,validationstring):
        #VALIDATION
        if(self.secretstring == validationstring):
            self.nodes.append(Node(node['host'], node['port']))
            print("Attached node {} {}".format(node['host'],node['port']))

            return str("OK")
        else:
            return 'Validation error'

    def detach(self,node,validationstring):
        if(self.secretstring == validationstring):
            # self.nodes = [attached_node for attached_node  in self.nodes if attached_node.host != node['host'] and attached_node.port  != node['port']]
            for i in range(len(self.nodes)):
                if(self.nodes[i].host == node['host'] and self.nodes[i].port == node['port']):
                    self.nodes.pop(i)
            print("Detached node {} {}".format(node['host'],node['port']))
            return "OK"
        else:
            return "Validation error"
    

class SimpleThreadedXMLRPCServer(ThreadingMixIn, SimpleXMLRPCServer):
    pass

if __name__ == '__main__':
    try:
        ServerManager().run_server()
    except KeyboardInterrupt:
        print('Exiting')
        sys.exit(0)

    except Exception:
        print('ERROR')
        sys.exit(1)
  