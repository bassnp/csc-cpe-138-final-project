# client.py

# Argparse handles proper parameters before execution 
import argparse

# Socket offers network interconnectivity as a client
from socket import *

# Threading allows for handling of inbound and outbound runtimes
from threading import *

# Class for connecting clients
class Client:
    def __init__(self, host, port):
        self.host = host
        self.port = port
        
    # Inbound traffic
    def inbound(self, sock):
        while True:
            try: # Receive 'data' inbound for displaying
                data = sock.recv(2048).decode("utf-16")
                if data:
                    print(data, end = "")
                else:
                    break
            
            except Exception as err:
                break

    # Outbound traffic    
    def outbound(self, sock):
        while True:
            try: # Send input 'msg' outbound to the server
                msg = input("")
                sock.sendall(msg.encode("utf-16"))
            except Exception as err:
                break

    # Maintain connections so if it drops, the threads will drop
    def maintain(self, sock):
        # Create 'daemon' threads (aka low-priority/background thread)
        inbound_handle = Thread(target = self.inbound, args = (sock,), daemon = True)
        outbound_handle = Thread(target = self.outbound, args = (sock,), daemon = True)
        
        inbound_handle.start()
        outbound_handle.start()
        
        # If inbound or outbound connection drops, stop both threads
        while True: 
            if not inbound_handle.is_alive() or not outbound_handle.is_alive():
                break # Exit route
        
    # Create a connection to host and port
    def establish(self):
        client = socket(AF_INET, SOCK_STREAM)
        client.connect((self.host, self.port))

        # Client runtime
        try: 
            connection = Thread(target = self.maintain, args = (client,), daemon = False)
            connection.start()
            # Await disconnect
            connection.join()

        # Extraordinary error handling
        except Exception as err: 
            print(f"Timed out: {err}")
            
        # Clean up on disconnect
        finally: 
            client.close()
            print(f"\nClosed connection to {self.host}")
            exit()

# Start
def main():
    # Handle args so proper parameters are met
    parser = argparse.ArgumentParser()
    parser.add_argument("hostname", type = str, help = "Hostname of server")
    parser.add_argument("svr_port", type = int, help = "Server port")
    args = parser.parse_args()
        
    # Modular clients connections
    client1 = Client(args.hostname, args.svr_port)
    client1.establish() 
    
if __name__ == "__main__":
    main()
