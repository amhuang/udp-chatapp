import click
import subprocess
import server
import client

class myCmd(click.Command):
    def parse_args(self, ctx, args):
        if len(args) == 0:
            raise click.UsageError("Please specify client or server mode to run the chatapp.")

        elif args[0] == "-s":
            if len(args) == 1:
                raise click.UsageError("Server's listening port number is required.")
            args.insert(1, '')
            args.insert(2, '')
            args.insert(4, '0')

        elif args[0] == "-c":
            if len(args) != 5:
                raise click.UsageError("Client name, server IP address, server’s listening port number, and client's listening port number are required.")

        super(myCmd, self).parse_args(ctx, args)

@click.command(cls=myCmd)
@click.option("-s", is_flag=True, default=False, help="Runs chatapp server")
@click.option("-c", is_flag=True, default=False, help="Runs chatapp client")
# arguments for client mode
@click.argument("name", required=False, type=str)
@click.argument("server-ip", required=False, type=str)
@click.argument("server-port", required=False, type=int)    # arg for server mode
@click.argument("client-port", required=False, type=int)
def cli(s, c, name, server_ip, server_port, client_port): # name, server_ip,
    '''
    Required for server mode:
    SERVER_PORT     The port the server is listening on.

    Required for client mode:
    SERVER_PORT     The port the server is listening on.
    CLIENT_PORT     The port the client is listening on.
    '''
    if s and not c:
        '''if not server_port:
             click.echo("Please specify server listening port")'''
        #click.echo(server_port)
        server.run(server_port)
    elif c and not s:
        client.run(name, server_ip, server_port, client_port)
    else: 
        click.echo("Please specify client or server mode to run the chatapp")