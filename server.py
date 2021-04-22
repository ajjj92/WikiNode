import random
import time
from socketserver import ThreadingMixIn
from xmlrpc.server import SimpleXMLRPCServer
import xmlrpc.client
import sys
from threading import Thread
import requests
import threading, queue
import multiprocessing
import os
from multiprocessing import Manager
from multiprocessing.pool import ThreadPool
import json
from collections import deque
import time
import uuid

URL = "https://en.wikipedia.org/w/api.php"

class Node:
    def __init__(self,host,port):
        self.host = host
        self.port = port

class WorkerManager():
    def __init__(self,start,finish):
        self.start = start
        self.finish = finish

    def validate_path(self):
        S = requests.Session()

        R = S.get(url=URL, params={
            "action": "query",
            "format": "json",
            "list": "search",
            "srsearch": self.start
        })
        start_data = R.json()

        R = S.get(url=URL, params={
            "action": "query",
            "format": "json",
            "list": "search",
            "srsearch": self.finish
        })

        finish_data = R.json()
        if start_data ['query']['search'][0]['title'] == self.start and finish_data ['query']['search'][0]['title'] == self.finish:
            return True
        else:
            return False
    
    def result(self,path,start,end):
        if path:
            result = path
        else:
            result = "No path"
        d = {"start": start, "end": end, "path": path}
        return json.dumps(d, indent=4)  

    def find_shortest_path(self,start, end):
        path = Manager().dict()
        path[start] = [start]
        Q = deque([start])
        while len(Q) != 0:
            page = Q.popleft()
            # links = get_links(page)
            links = self.get_neighbour_links(page)
            workers = len(links)
            if(workers == 0):
                workers = 1
            pool = ThreadPool(processes=workers)
            results = [pool.apply(self.thread_populate, args=(path, page, link, end)) for link in links]
            pool.terminate()
            for result in results:
                if type(result) == list:
                    return result
                Q.append(result)

    def get_neighbour_links(self,title):
        S = requests.Session()
        PARAMS = {
            "action": "query",
            "format": "json",
            "titles": title,
            "prop": "links",
        }
        time.sleep(0.04)
        R = S.get(url=URL, params=PARAMS)
        neighbour_data= R.json()
        link_titles = []
        try:
            data = neighbour_data.get('query').get('pages')
            for k in data:
                if(k !='-1'):
                    links = data[k].get('links')
                    for v in links:
                        link_titles.append(v.get('title'))
            return link_titles
        except AttributeError:
            return []

    def thread_populate(self,path, page, link, end):
        if link == end:
            return path[page] + [link]
        if (link not in path) and (link != page):
            path[link] = path[page] + [link]
            return link

class Server():

    def run_server(self,host,port):
        server_addr = (host, port)
        server = SimpleThreadedXMLRPCServer(server_addr)
        server.register_function(find_path, 'find_path')

        server.register_introspection_functions()
        print('listening on {} port {}'.format(host, port))
        print("Node server started")
        server.serve_forever()
  
class SimpleThreadedXMLRPCServer(ThreadingMixIn, SimpleXMLRPCServer):
    pass


def find_path(start,end):
    
    worker_manager = WorkerManager(start,end)
    if(worker_manager.validate_path()):
        path = worker_manager.find_shortest_path(start, end)
        json_result = worker_manager.result(path, start, end)
        print(json_result)
        return json_result
    else:
        return 'Validation Error'


if __name__ == '__main__':

    if len(sys.argv) != 3:  
        print ("Usage: script, IP address, port number") 
        exit()
    # Create and start server thread
    with xmlrpc.client.ServerProxy("http://localhost:8000/", allow_none=True) as proxy:
        print(proxy)
        try:
            host = str(sys.argv[1])
            port = str(sys.argv[2])
            print("Attaching node to NodeManager...")
            node_manager_result = proxy.attach(Node(host,port),'abbcvfffd32xXx123')
            if(node_manager_result == 'OK'):
                print("Attached to NodeManager")
                print ("Starting Node...") 
                server = Server()
                server.run_server(str(sys.argv[1]),int(sys.argv[2]))
        except xmlrpc.client.Error as er:
            print("ERROR", er)
            sys.exit(1)
        except KeyboardInterrupt:
            print("Exiting..")
            result = proxy.detach(Node(host,port),'abbcvfffd32xXx123')
            if(result == 'OK'):
                print ("Detached Node...") 
            else:
                print('Error Detacching')
            sys.exit(0)
        except Exception:
            print('Attaching Node failed.')
            sys.exit(1)

        