# server.py
# This program wil implement the center broker (server) that manages all communication
# between clients in the distributed chat system.

import socket
import threading
import json

from json_log import log_event # integrate logging into the broker

HOST = "127.0.0.1"
PORT = 3002

# holds dictionary that maps client sockets to userusername
clients = {} # socket => username
user_sockets = {} # username => socket
subscriptions = {} # topic => set of users

def handle_clients(connection, address):
    try:
        # server receives registration packet
        registration_packet = json.loads(connection.recv(1024).decode())
        username = registration_packet["username"]
        
        clients[connection] = username
        user_sockets[username] = connection
        
        log_event("connection", username)
        print(f"[REGISTRATION] {username} has joined")
        
        join_packet = {
            "type": "user_joined",
            "payload": username,
        }
        
        for sock in clients:
            if sock != connection:
                sock.send(json.dumps(join_packet).encode())
    
        while True:
            data = connection.recv(1024)
            if not data:
                break
        
            try:
                packet = json.loads(data.decode())
            except json.JSONDecodeError: 
                print("[ERROR] Invalid packet received")
                continue
        
            route_message(connection, packet)
        
    except Exception as e:
        print(f"[ERROR] {e}")
        
    finally:
        # clean the connection and remove the registry
        if connection in clients:
            username = clients[connection]
            del clients[connection]
            del user_sockets[username]
        connection.close()
        
        log_event("disconnection", {username})
        print(f"[DISCONNECTION] {username} left")

# routing logic based on display, direct_message (DM), topics, groups, or channels
def route_message(sender_connection, packet):
    message_type = packet["type"]
    sender = clients[sender_connection]
    
    if message_type == "chat":
        log_event("message", sender, packet)
        display(sender_connection, packet)
        
    elif message_type == "direct":
        log_event("direct_message", sender, packet)
        send_to_user(packet["to"], packet)
        
    elif message_type == "subscribe":
        topic = packet["topic"]
        log_event("subscription", sender, packet)
        subscriptions.setdefault(topic, set()).add(sender)
        
    elif message_type == "publish":
        topic = packet["topic"]
        log_event("publish", sender, packet)
        publish(topic, packet)
    
# function will send a given message to all connected clients except the sender => achieves 'broker-based routing' - no direct client-to-client links
def display(sender_connection, packet):
    message = json.dumps(packet).encode()
    for connection in clients:
        if connection != sender_connection:
            connection.send(message)

# supports direct messages
def send_to_user(username, packet):
    if username in user_sockets:
        user_sockets[username].send(json.dumps(packet).encode())
        
def publish(topic, packet):
    if topic in subscriptions:
        for user in subscriptions[topic]:
            user_sockets[user].send(json.dumps(packet).encode())
     
# function will initialize the broker, bind it to a network port, and consistently accept new client connections   
def start_server():
    # create a tcp/ip socket
    server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    
    # bind the socket to the local machine and a port
    server.bind(('localhost', 3002))
    server.listen() # listen for incoming connections
    print(f"[BROKER STARTED] {HOST}:{PORT}...")
    
    while True: # accepts new clients and assign each to its own thread
        connection, address = server.accept()
        thread = threading.Thread(target=handle_clients, args=(connection, address))
        thread.start()
        print(f"[ACTIVE CONNECTIONS] {threading.active_count() - 1}")
        
if __name__ == '__main__':
    start_server()