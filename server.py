# server.py

# Argparse handles proper parameters before execution 
import argparse

# Socket offers network interconnectivity as a host server
from socket import *

# Threading allows for handling of multiple instances of runtimes
from threading import *

# Basic server class
class ChatServer:
    # Create a hosted server and open a port
    def __init__(self):
        self.host = "localhost"
        self.port = -1
        self.sock = None
        
        # Database
        self.clients  = {} # Dictionary of Client objects index by their respective address 'adrs'
        self.users = {} # Dictionary of pointers to 'clients' indexed by their respective 'name' (kinda like a foreign-key map onto 'clients')

    def maintain(self, port):
        try:
            self.sock = socket(AF_INET, SOCK_STREAM)
            self.sock.bind((self.host, port))
            self.sock.listen(10)
            print(f"\n{{DEBUG}} Server established: {self.sock.getsockname()}\n")
            
            # Server runtime - Allow for clients to connect
            while True:
                try:
                    if len(self.clients) < 10: # Maximum of 10 connections at a time
                        print("{{DEBUG}} Awaiting next client...")
                        new_sock, new_adrs = self.sock.accept()
                        self.broadcast(f"Accepting new client: {new_sock.getpeername()}")
                        
                        # Since the tokenizer only takes ensures theres no spaces in the name, i added a space in the uninitialized name used to decern whether or not a client has registered as a user
                        self.clients[new_adrs] = User(new_sock, new_adrs, "Unknown User", self)
                        Thread(target = self.clients[new_adrs].create, daemon = True).start()
                        
                except Exception as err:
                    print(f"{{DEBUG}} Runtime error: {err}")
                    break
        except Exception as err:
            print(f"{{DEBUG}} Establishing error: {err}")
        
    def open(self, port):
        chatroom = Thread(target = self.maintain, args = (port,), daemon = False)
        chatroom.start()

    def drop(self):
        self.sock.close()

    # Braodcasts desired message to all registered clients
    def broadcast(self, message, is_server = None):
        # Make server derived braodcasts unique
        if is_server:
            message = "[Server] " + message
        
        # Send data to all other registered clients
        for adrs in list(self.clients):
            client = self.clients[adrs]
            try:
                client.dm(message)
                print(f"{{DEBUG}} {message}")
                
            except Exception as err: 
                print(f"{{DEBUG}} {client.name} timed out: {err}")
                client.drop()
        
# Client handler class for organzing client related data
class User:
    # Constructor
    def __init__(self, sock, adrs, name, server):
        self.sock = sock
        self.adrs = adrs
        self.name = name
        self.server = server
        
    # Drops specified client from all data entries
    def drop(self):
        if self.name != "Unknown User":
            del self.server.users[self.name]
        del self.server.clients[self.adrs]
        self.sock.close()

    # Directly Message a specified client with a message
    def dm(self, message):
        message = f"{message}\n"
        self.sock.sendall(message.encode("utf-16"))
    
        server_msg = message.replace("\n"," ")
        print(f"{{DEBUG}} {self.name} => {server_msg}")
        
    # Maintain connection to respective server
    def maintain(self):
        adrs, sock, server = self.adrs, self.sock, self.server
        try:
            while True: 
                data = sock.recv(2048).decode("utf-16")
                if not data:
                    print(f"{{DEBUG}} {adrs} disconnected")
                    break
                
                # Tokenize command and its possible arguments for interpreting
                tokens = data.split(" ")
                comd = tokens[0].lower()
                
                # Make sure clients join with a name
                if self.name == "Unknown User":
                    if comd == "join": 
                        name = tokens[1]
                        if list(server.users.keys()).count(name) == 0:
                            server.clients[adrs].name = name
                            server.users[name] = server.clients[adrs] # Make pointer to value of Client in clients by making 'name' a foreign key
                            server.broadcast(f"'{name}' has joined the chatroom! {sock.getpeername()}", True)
                            self.dm("Type 'help' for a list of commands.")
                        else:
                            self.dm("That name was already taken, please use another name and try again.")
                    elif comd == "quit":  
                        server.broadcast(f"{sock.getpeername()} has stopped connecting.", True)
                        break
                    else:
                        self.dm("YOU DO NOT HAVE A NAME! Please use the command 'JOIN <username>' before continuing.")
                else:
                    if comd == "help":                
                        self.dm("\tHELP - Lists all available commands.\n\tLIST - Lists everyone in the chatroom.\n\tMESG <username> <message> - Messages any valid specified <username> with the <message>.\n\tBCST <message> - Broadcasts a message to everyone in the chatroom.\n\tQUIT - Closes the connection to the chatroom.")
                    elif comd == "join": 
                        self.dm("You have already registered, you cannot use 'JOIN'.")
                    elif comd ==  "list": 
                        self.dm(f"Users: {str(list(server.users.keys()))[1:-1]}") # lol
                    elif comd ==  "mesg": 
                        # Validate parameters, etc.
                        if len(tokens) < 3:
                            self.dm("Invalid usage of MESG, please type 'help'.")
                        else:
                            target = tokens[1]
                            if list(server.users.keys()).count(target) > 0:
                                server.users[target].dm(f"[Direct] '{name}': {data[6 + len(target):]}") # 0_0
                            else:
                                self.dm("Invalid name for MESG, please type 'list'.")
                    elif comd ==  "bcst": 
                        msg = data[5:]
                        if len(msg) > 0:
                            server.broadcast(f"[Chat] {name}: {data[5:]}", False)
                        else:
                            self.dm("Invalid usage of BCST, please type 'help'.")
                    elif comd ==  "quit": 
                        server.broadcast(f"'{name}' has left the chatroom!", True)
                        break
                    else:
                        self.dm(f"'{comd}' is not a command! Please see use 'help' to find the list of commands.")
                            
        # Catch timed out clients given any reason
        except Exception as err:
            print(f"{{DEBUG}} {self.name} timed out: {err}")
            
        # Clean up and disconnect
        finally: 
            self.drop()
            
    # Create a client from a conneciton
    def create(self):
        # Initial messages sent on connect 
        self.server.broadcast(f"Someone is connecting: {self.sock.getpeername()}", True)
        self.dm("\nWelcome to the chatroom!\n------------------------")
        self.dm("YOU DO NOT HAVE A NAME! Please use the command 'JOIN <username>' before continuing.")
        
        # Start of entire client runtime
        user = Thread(target = self.maintain, daemon = True)
        user.start()
   
# Start
def main():
    # Handle args so proper parameters are met
    parser = argparse.ArgumentParser()
    parser.add_argument("svr_port", type = int, help = "Port to open sever with")
    args = parser.parse_args()
        
    # I like using ports between 9120 - 9140, idky
    chatroom = ChatServer()
    chatroom.open(args.svr_port)
    
    # MODULARITY?! :O
    # chatroom2 = ChatServer()
    # chatroom2.open(9130)
    
if __name__ == "__main__":
    main()