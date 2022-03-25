import click
import subprocess
import server
import client
import ipaddress

class chatCommand(click.Command):
    def parse_args(self, ctx, args):
        if len(args) == 0:
            raise click.UsageError("Please specify client or server mode to run the chatapp.")

        elif args[0] == "-s":
            if len(args) == 1:
                raise click.UsageError("Server's listening port number is required.")
            args.insert(1, '')
            args.insert(2, '')
            args.insert(4, '0')
            self.valid_port(args[3]) # Validate server port

        elif args[0] == "-c":
            if len(args) != 5:
                raise click.UsageError("Client name, server IP address, server’s listening port number, and client's listening port number are required.")
            if not args[1].isalnum():
                raise click.UsageError("Client name can only include alphanumeric characters.")

            self.valid_ip(args[2])
            self.valid_port(args[3]) # Validate server port
            self.valid_port(args[4]) # Validate client port
           
        super(chatCommand, self).parse_args(ctx, args)

    def valid_port(self, port):
        if int(port) < 1024 or 65535 < int(port):
            raise click.UsageError("Port numbers must be in the range 1024-65535.")

    def valid_ip(self, addr):
        try:
            ip = ipaddress.ip_address(addr)
        except ValueError:
            raise click.UsageError("Please provide a valid IP address for the server.")

@click.command(cls=chatCommand)
@click.option("-s", is_flag=True, default=False, help="Runs chatapp server")
@click.option("-c", is_flag=True, default=False, help="Runs chatapp client")
# arguments for client mode
@click.argument("name", required=False, type=str)
@click.argument("server-ip", required=False, type=str)
@click.argument("server-port", required=False, type=int)    # arg for server mode
@click.argument("client-port", required=False, type=int)
def cli(s, c, name, server_ip, server_port, client_port): # name, server_ip,
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
    
    if s and not c:
        server.run(server_port)
    elif c and not s:
        #client = Client()
        client.run(name, server_ip, server_port, client_port)
    else: 
        click.echo("Please specify client or server mode to run the chatapp.")