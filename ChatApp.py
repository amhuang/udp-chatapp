import click
import subprocess
import server
from client import Client
import ipaddress
import sys

"""
    \b
    Required for server mode:
    SERVER_PORT     The port the server is listening on.

    \b
    Required for client mode:
    NAME            The client name.
    SERVER_IP       The server's IP address.
    SERVER_PORT     The port the server is listening on.
    CLIENT_PORT     The port the client is listening on.
"""

class ChatApp:
    def run(self):
        if len(sys.argv) < 3:
            print("Usage: python3 ChatApp.py <mode> <args>")
            sys.exit(1)

        if sys.argv[1] == "-s" and len(sys.argv) == 3:
            server_port = int(sys.argv[2])
            self.validate_port(server_port)
            server.run(server_port)

        elif sys.argv[1] == "-c" and len(sys.argv) == 6:
            name = sys.argv[2]
            server_ip = sys.argv[3]
            server_port = int(sys.argv[4])
            client_port = int(sys.argv[5])
            self.validate_name(name)
            self.validate_ip(server_ip)
            self.validate_port(server_port)
            self.validate_port(client_port)
            client = Client(name, server_ip, server_port, client_port)
            client.run()
        
        else:
            print("Usage: python3 ChatApp.py <mode> <args>")
            sys.exit(1)

    def validate_name(self, name):
        if not name.isalnum():
            print("Client name must consist of alphanumeric characters.")
            sys.exit(1)

    def validate_port(self, port):
        if int(port) < 1024 or 65535 < int(port):
            print("Port numbers must be in the range 1024-65535.")
            sys.exit(1)
        
    def validate_ip(self, addr):
        try:
            ip = ipaddress.ip_address(addr)
        except ValueError:
            print("Please provide a valid IP address for the server.")
            sys.exit(1)

chatapp = ChatApp()
chatapp.run()