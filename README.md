# CSEE 4119 PA1: UDP Simple Chat Application
Name: Andrea Huang
UNI: amh2341

# Using the Chat App
Run the server mode of chat app in the project directory with the following command:
```
$ python3 ChatApp.py -s <port>
```

Run one or more instances of client mode for chat app:
```
$ chatapp -c <name> <server-ip> <server-port> <client-port> 
```

This command line application only uses packages built into Ubuntu and Python 3, so there are no additional dependencies that need to be used. 

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