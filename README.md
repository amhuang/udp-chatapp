# CSEE 4119 PA1: UDP Simple Chat Application
Name: Andrea Huang

UNI: amh2341

--- 
## Using the Chat App
Run the server mode of chat app in the project directory with the following command:
```
$ python3 ChatApp.py -s <port>
```

Run one or more instances of client mode for chat app:
```
$ chatapp -c <name> <server-ip> <server-port> <client-port> 
```

This command line application only uses packages built into Ubuntu and Python 3, so no additional dependencies need to be installed. 

---
## Implementation

Each of the 5 required chat app functionalities have been implemented according to the project specs. The server also prints out messages informing the user of what actions it is taking. Any additional features are mentioned below.

### Protocol
Messages sent between the server and client or between clients use the following format: `<header>\n<data>`
- The header describes the purpose of the message.
    - Headers for server-client messages:
        - `reg`: registration request or ACKs
        - `dereg`: deregistration request or ACKs
        - `save`: offline message request or ACKs
        - `all`: group chat messages or ACKs
        - `hello`: server checking if client is alive
        - `saved`: offline messages saved for a client by the server
        - `table`: client table updates from server
    - Headers for client-client direct messages:
        - `msg`: Direct chat message
        - `ack`: ACK for direct chat
- The header and data are separated by `\n`.
- The data may be the message body, a client name, ACK, etc. The server and clients respond to the data accordingly based on the command.

### `ChatApp.py`
- Reads command line arguments and checks their validity.
    - A name is validated by checking if it is under 40 alphanumeric characters
    - An IP address is validated by checking if it can be convertd into an IPv4Address object
    - Port numbers are checked to be between 1024-66535 
- It then runs the program by instantiating a Client or Server object and calling `run()` on either.

### `server.py`
This defines a Server class which is created by `Chatapp.py` in server mode.

- Initialization
    - `run()` is called in `ChatApp.py` which binds the server's socket and starts a while loop to receive messages.
    - Incoming messages can have of a max length of 2048. This accomodates a message body of up to 2000 chars. The remaining 48 chars are reserved for client names (up to 40 chars) and the header (up to 6 chars).
    - The message header and body are split by `\n`, and the server takes appropriate action based on the header.

- Register
    - Initiated with a client message with header "reg." Client name taken from the message body.
    - The server calls `register(addr, name)` which checks if a client is in the client table by `name`. 
        - If it's not, the server adds it, broadcasts the table to all clients, and sends an ACK with a "reg" header.
        - If it is and its status in the table is  offline, the registration succeeds.
        - If it is but `addr` and the address in the table do not match, then another machine is trying to register with a client name that is taken. The server aborts the registration and notifies the client.
        - If it is and `addr` matches the address in the table, then the server didn't know that the client had gone offline. The table is broadcasted.

- Deregister
    - Initiated with a client message with header "dereg." Client name taken from the message body.
    

- Offline messages

- Group chat

- Broadcast table updates

### `client.py`
The client runs on two threads: one for processing user input, one for receiving messages from the server and client.

- Initialization
    - 

- Register
    - Initiated with user input starting with "reg ".
        - If the remainder of the input matches the client's name and the client is not online (stored as class attributes), client calls `register()`.
        - If the client is already online, the prompt notifies the user and registration terminates.
        - Otherwise, the client is notified that it can only register with its own name and  registration terminates.
    - `register()`
        - Sends server registration request with "reg" header and client name in body.
        - Waits up to 500ms to receive a broadcasted table from the server which indicates successful registration.
    - If the client receives a message from the server with header "reg" and "ERR" in the body, then the client name has already been taken by another user. The program quits so the user can start a client with a different name.

- Deregister
    - 

- Direct chat

- Offline messages

- Group chat


## Chat App Functionalities


### Direct chat
```
>>> send <name> <message>
```
### Group chat:
send message to all clients:
```
>>> send_all <message>
```
### Deregister (go offline)
```
>>> dereg <nickname>
```
###  Re-register (return online)
```
>>> reg <nickname>
```

### Offline Chat

## Known Bugs

- The main bug is an issue with only one ">>>" showing up in front of each prompt or message for the client. Sometimes, there may be two or none. This is due to the receiving and input threads running concurrently. For instance, the ">>>" prompt from the input function may print once, then another ">>>" may print in front of it because of an application prompt in response to a message received 

- Otherwise, I tested all the required functionalities and error catching to the best of my ablities, and I have not found any bugs. 


## Tests

The text output for tests are provided in the specs are provided in `test.txt`. Tests 1-3 are replicas of the ones provided in the notes. 

Test 4: Detecting silent leave via send_all
- Start server
- Start client x
- Start client y
- Start client z 
- ctrl-c x
- send_all by y (server doesn't get an ack from x, updates table and broadcasts)

Test 4:
- Start server
- Start client x
- Start client y
- Start client z 
- dereg y
- send_all by x
- send z -> y
- reg y

