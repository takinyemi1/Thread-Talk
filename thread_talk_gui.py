import socket
import threading
import json
import tkinter as tk
from tkinter import scrolledtext, simpledialog, messagebox

class ClientGUI:
    def __init__(self, master):
        self.master = master
        master.title("ThreadTalk Chat Client")

        # layout
        self.chat_area = scrolledtext.ScrolledText(master, wrap=tk.WORD, state='disabled', width=50, height=20)
        self.chat_area.pack(padx=10, pady=10)

        self.entry = tk.Entry(master, width=40)
        self.entry.pack(side=tk.LEFT, padx=10, pady=5)
        self.entry.bind("<Return>", self.send_message)

        self.send_button = tk.Button(master, text="Send", command=self.send_message)
        self.send_button.pack(side=tk.LEFT)

        # network
        self.client = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        try:
            self.client.connect(('localhost', 3002))
        except:
            messagebox.showerror("Connection Failed", "Unable to connect to broker.")
            master.destroy()
            return

        # ask for username
        username = simpledialog.askstring("Username", "Enter a username >> ")
        if not username:
            master.destroy()
            return

        self.username = username

        # register with the broker
        reg_packet = {
            "type": "register",
            "username": username
        }
        self.client.send(json.dumps(reg_packet).encode())

        # start receiver thread
        recv_thread = threading.Thread(target=self.receive_loop, daemon=True)
        recv_thread.start()

    # receive messages from the server
    def receive_loop(self):
        while True:
            try:
                msg = self.client.recv(1024).decode()
                if not msg:
                    break

                packet = json.loads(msg)
                mtype = packet.get("type")
                payload = packet.get("payload")

                if mtype == "chat":
                    self.display_message(payload)
                elif mtype == "user_joined":
                    self.display_message(f"[SYSTEM] {payload} has joined the chat!")
                else:
                    self.display_message(f"[SYSTEM] {payload}")

            except:
                self.display_message("[ERROR] Lost connection to server.")
                break

    # display message in the chat area
    def display_message(self, message):
        self.chat_area.config(state='normal')
        self.chat_area.insert(tk.END, message + "\n")
        self.chat_area.config(state='disabled')
        self.chat_area.yview(tk.END)

    # send chat message to broker
    def send_message(self, event=None):
        text = self.entry.get()
        if not text.strip():
            return

        packet = {
            "type": "chat",
            "payload": f"{self.username}: {text}"
        }

        try:
            self.client.send(json.dumps(packet).encode())
            # display message locally immediately
            self.display_message(f"{self.username}: {text}")
        except:
            self.display_message("[SEND ERROR] Could not send.")
            return

        self.entry.delete(0, tk.END)


# main entry
if __name__ == "__main__":
    root = tk.Tk()
    gui = ClientGUI(root)
    root.mainloop()