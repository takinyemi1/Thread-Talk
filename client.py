# Program: client.py
# This client connects to the central Broker (server.py) and allows the user to send and receive chat messages
# simultaneously using threads.

import socket
import threading
import json

# function will continuously run in the background while listening for any incoming messages from the broker (server) and immediately prints them
def receive(sock):
    while True:
        try:
            message = sock.recv(1024).decode()
            if not message:
                # if there is no message received, the server most likely closed the connection
                print("[BROKER DISCONNECTION] Disconnected from the server.")
                break
            
            packet = json.loads(message)
            
            message_type = packet.get("type")
            payload = packet.get("payload")
            
            if message_type == "chat":
                print(f"[MESSAGE RECEIVED] {payload}") # only shows the message to the user
                
            elif message_type == "system":
                print(f"[SYSTEM] {payload}")
                
        except:
            # handles errors like broker (server) shutdown or network drop
            print("[ERROR] Error occurred while receiving messages.")
            break
        
# sends JSON packets with metadata
def send(sock):
    while True:
        message = input("Enter a message. \n>> ") # user will enter a message
        packet = {
            "type": "chat",
            "payload": message,
        }
                
        try:
            sock.send(json.dumps(packet).encode()) # encode and send the message to the broker
        except: 
            print("[SEND ERROR] Unable to send message. Connection has been lost.")
            break
        
# function will be the main entry point for the client program
#  it will connect to the broker using TCP, authenticate with a username, and generate two threads (sender and receiver)
def start_client():
    # create tcp/ip socket
    client = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    
    # connect to the broker (central server)
    # replace the 'localhost' and 3002 with the broker IP and port if running remotely
    client.connect(('localhost', 3002))
    print("[CONNECTED] Connected to the broker at localhost:3002")
    
    # identify the client with a username (authentication)
    username = input("Enter username. \n>> ")
    client.send(json.dumps({
        "type": "register",
        "username": username,    
    }).encode()) # send the username to the broker as JSON
    
    # generate two threads
    #  receiver thread to run receive() to consistently print incoming messages
    # sender thread to run send() to allow simultaneous user input
    receiver_thread = threading.Thread(target=receive, args=(client,))
    sender_thread = threading.Thread(target=send, args=(client,))
    
    # start both threads
    receiver_thread.start()
    sender_thread.start()
    
    # run the thread indefinitely until the user disconnects or the broker (server) just stops
    receiver_thread.join()
    sender_thread.join()
    
    # close the connection when both threads terminate
    client.close()
    
if __name__ == '__main__':
    start_client()