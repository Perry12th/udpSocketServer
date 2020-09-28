import random
import socket
import time
from _thread import *
import threading
from datetime import datetime
import json

clients_lock = threading.Lock()
connected = 0

clients = {}

def connectionLoop(sock):
   while True:
      data, addr = sock.recvfrom(1024)
      data = str(data)
      if addr in clients:
         if 'heartbeat' in data:
            clients[addr]['lastBeat'] = datetime.now()
      else:
         if 'connect' in data:
            clients[addr] = {}
            clients[addr]['lastBeat'] = datetime.now()
            clients[addr]['color'] = 0
            
            #Create a small list for the players in game (Not for the new client though)
            IO_Players = {"cmd" : 0, "players": []}
            player = {}
            player["id"] = str(addr)
            IO_Players['players'].append(player)
            m = json.dumps(IO_Players)
            for c in clients:
               if c != addr:
                   sock.sendto(bytes(m,'utf8'), (c[0], c[1]))

            #Create a whole list of players for the new client to make
            IO_Players = {"cmd" : 0, "players": []}
            for c in clients:
               player = {}
               player["id"] = str(c)
               IO_Players['players'].append(player)
            m = json.dumps(IO_Players)
            
            sock.sendto(bytes(m,'utf8'), (addr[0], addr[1]))

def cleanClients(sock):
   while True:
      IO_Players = {"cmd" : 2, "players": []}
      for c in list(clients.keys()):
         if (datetime.now() - clients[c]['lastBeat']).total_seconds() > 5:
            print('Dropped Client: ', c)
            player = {}
            player["id"] = str(c)
            IO_Players['players'].append(player)
            clients_lock.acquire()
            del clients[c]
            clients_lock.release()
      if (IO_Players.get("players") != []):
         clients_lock.acquire()
         m = json.dumps(IO_Players)
         for c2 in clients:
            sock.sendto(bytes(m, 'utf8'), (c2[0],c2[1]))
         print('Dropped Client Message Sent')
         clients_lock.release()
      time.sleep(1)

def gameLoop(sock):
   while True:
      GameState = {"cmd": 1, "players": []}
      clients_lock.acquire()
      print (clients)
      for c in clients:
         player = {}
         clients[c]['color'] = {"R": random.random(), "G": random.random(), "B": random.random()}
         player['id'] = str(c)
         player['color'] = clients[c]['color']
         GameState['players'].append(player)
      s=json.dumps(GameState)
      print(s)
      for c in clients:
         sock.sendto(bytes(s,'utf8'), (c[0],c[1]))
      clients_lock.release()
      time.sleep(1)

def main():
   port = 12345
   s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
   s.bind(('', port))
   start_new_thread(gameLoop, (s,))
   start_new_thread(connectionLoop, (s,))
   start_new_thread(cleanClients,(s,))
   while True:
      time.sleep(1)

if __name__ == '__main__':
   main()
