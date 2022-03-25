# csee4119-pa1
 
This command line application is created using setuptools and click libraries. Please follow the instructions to set up a virtual environment in the main directory in order to use the ```chatapp``` command line interface,

```
$ virtualenv venv
$ . venv/bin/activate
$ pip install --editable .
```

# Starting the chatapp
Run the server mode of chat app:
```
$ chatapp -s <port>
```

Run one or more instances of client mode for chat app:
```
$ chatapp -c <name> <server-ip> <server-port> <client-port> 
```

# Chat App Commands
Direct chat: end a message to one user: 
```
>>> send <name> <message>
```
Group chat: send message to all clients:
```
>>> send_all <message>
```
Deregister (go offline): 
```
>>> dereg <nickname>
```
Re-register (return online): 
```
>>> reg <nickname>
```