# CSEE 4119 PA1: UDP Simple Chat Application
Name: Andrea Huang

UNI: amh2341

--- 
## Using the Chat App
You can run one instance of the server and multiple instances of clients from in the project directory. 

Run the server (server mode):
```
$ python3 ChatApp.py -s <port>
```

Run a client (client mode):
```
$ python3 ChatApp.py <name> <server-ip> <server-port> <client-port> 
```
Multiple clients can be added by running this command in other terminals using a different `<name>` and `<client-port>`.

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
    - `run()` is called on a Client object in `ChatApp.py` which binds the server's socket and starts a while loop to receive messages.
    - Incoming messages can have of a max length of 2048. This accomodates a message body of up to 2000 chars. The remaining 48 chars are reserved for client names (up to 40 chars) and the header (up to 6 chars).
    - The message header and body are split by `\n`, and the server takes appropriate action based on the header.

- Register
    - Initiated by receiving a client message with header "reg". This calls `register(addr, name)` with the address that sent the message and the name from the message body.
    - `register(addr, name)` 
        - Checks if a client is in the client table by `name`. 
        - If it's not, the server adds it and broadcasts the table to all clients.
        - If it is and its status in the table is offline, the registration succeeds.
        - If it is but `addr` and the address in the table do not match, then another machine is trying to register with a client name that is taken. The server aborts the registration and notifies the client.
        - If it is and `addr` matches the address in the table, then the server didn't know that the client had gone offline. The table is broadcasted.

- Deregister
    - Initiated with a client message with header "dereg". This calls `deregister(addr, name)` with the address that sent the message and the name from the message body.
    - `deregister(addr, name)`
        - Finds the client in the table by `name`.
        - Changes the client's status in the table to offline and sends an ACK with "dereg" in the header.
        - Broadcasts updated table to all clients.

- Offline messages
    - 

- Group chat

- Broadcast table updates

### `client.py`
The client runs on two threads: one for processing user input, one for receiving messages from the server and client.

- Initialization
    - `run()` is called on a Client in `ChatApp.py`. This binds the client socket to client_port, starts a thread that calls `recv()` for receiving messages, registers the client with `register()`, and calls `process_input()` to processing user input.
    - `recv()`
        - Accepts messages up to 2048 bytes. 
        - If the addr sending the message matches the server address, the client calls `recv_server()` to handle the messages. Otherwise, it calls `recv_client()` to handle direct chat messages.
    - `process_input()`
        - Reads and checks user input. If input is accepted, fulfills request by calling relevant functions. Otherwise, provides an error message to the user describing why input was rejected.
        - User commands:
            - `dereg <name>`: deregisters current client
            - `send <name> <message>`: sends direct or offline message to any client 
            - `send_all <message>`: sends message to entire channel (all clients online)
            - `reg <name>`: registers current client
            - `help`: prints help for all chat app commands

- Register
    - Initiated by `run()` when the client is first started or by user input starting with `>>> reg ...`
        - If the remainder of the input matches the client's name and the client is not online (stored as class attributes), the client calls `register()`.
        - If the client is already online or is trying to register with a different name, the prompt notifies the user and registration terminates.
    - `register()`
        - Sends server registration request with "reg" header and client name in body.
        - Waits up to 500ms to receive a broadcasted table from the server which indicates successful registration.
    - If the client receives a message from the server with header "reg" and "ERR" in the body, then the client name has already been taken by another user. The program quits so the user can start a client with a different name.

- Deregister
    - Initiated by user input starting with `>>> dereg ...`
        - If the rest of the input matches the users name and the user is currently online, the Client calls `deregister()`.
        - Otherwise, the user is notified that the client is already offline or that it can only register with its own name and deregistration terminates.
    - `deregister()`
        - Attempts to send dereg request to server up to 5 times. An attempt times out if an ACK isn't received in 500ms. 
        - Timeout was implemented with `time.time()` and a loop checking the boolean class attribute `acked` which is flipped to True if the client receives an ACK with a "dereg" header.


- Direct chat
    - 

- Offline messages
    - 

- Group chat
    - 

### Offline Chat

## Known Bugs

- The main bug is an issue with only one ">>>" showing up in front of each prompt or message for the client. Sometimes, there may be two or none. This is due to the receiving and input threads running concurrently. For instance, the ">>>" prompt from the input function may print once, then another ">>>" may print in front of it because of an application prompt in response to a message received 

- Otherwise, I tested all the required functionalities and error catching to the best of my ablities, and I have not found any bugs. 


## Tests

The text output for tests are provided in the specs are provided in `test.txt`. Tests 1-3 are the outputs for the 3 test cases provided in the specs.

Test 4: Stored messages for direct and group chats to an offline client
- Start server
- Start client x
- Start client y
- Start client z 
- dereg y
- send_all by x
- send z -> y
- reg y

Test 5: Detecting silent leave via send_all
- Start server
- Start client x
- Start client y
- Start client z 
- Silent leave by x
- send_all by y (server doesn't get an ack from x, updates table and broadcasts)



