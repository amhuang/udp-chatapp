# CSEE 4119 PA1: UDP Simple Chat Application
Name: Andrea Huang

UNI: amh2341

## Using the Chat App
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

## Protocol
Messages sent between the server and client or between clients use the following format: `<header>\n<data>`.
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
- The data may be the message body, a client name, ACK, etc. The server and clients respond to the data accordingly based on the command. For some features, the data includes both a client name and message. These are separated by`\n`.
- Server and Client receive incoming messages of up to 2048 bytes in length. This accomodates a message body of up to 2000 chars. The remaining 48 chars are reserved for client names (up to 40 chars), the header (up to 5 chars), and up to two `\n` separating the header from the message body and/or the client name from the message.

## Implementation

Each of the 5 required chat app functionalities have been implemented according to the project specifications. The server also prints out messages informing the user of what actions it is taking. Any additional features are mentioned below.

### `ChatApp.py`
- Reads command line arguments and checks their validity.
    - A name is validated by checking if it consists of 40 of fewer alphanumeric characters.
    - An IP address is validated by checking if it can be convertd into an IPv4Address object.
    - Port numbers are checked to be between 1024-66535.
- It then runs the program by instantiating a Client or Server object and calling `run()` on either.

### `server.py`
Defines a Server class which is created in server mode by `Chatapp.py`.

#### Initialization
- `run()` is called on a Server object in `ChatApp.py` which binds the server's socket and starts a while loop to receive messages. Accepts messages up to 2048 bytes. 
- The message header and body are split by `\n`, and the server takes appropriate action based on the header.

#### Register
- Initiated by receiving a client message with header `reg`. This calls `register(addr, name)` with the address that sent the message and the name from the message body.
- `register(addr, name)` 
    - Checks if a client is in the client table by `name`. 
    - If it's not, the server adds it and broadcasts the table to all clients.
    - If it is and its status in the table is offline, the registration succeeds and an updated table is broadcasted.
    - If it is but `addr` and the address in the table do not match, then another machine is trying to register with a client name that is taken. The server aborts the registration and notifies the client of the error.
    - If it is and `addr` matches the address in the table, then the server didn't know that the client had gone offline. The table is broadcasted.

#### Deregister
- Initiated by a client message with header `dereg`. This calls `deregister(addr, name)` with the address that sent the message and the name from the message body.
- `deregister(addr, name)`
    - Finds the client in the table by `name`.
    - Changes the client's status in the table to offline and sends an ACK with header `dereg`.
    - Broadcasts updated table to all clients.

#### Offline Messages
- Saving messages
    - Initiated by a client message with header `save` by calling `save_msg_recv()`. 
    - `save_msg_recv(addr, data)`
        - Gets recipient name and status from client table using `addr`.
        - If recipient is offline, server saves the message by calling `save_msg()` and sending an ACK with header "save" to `addr`. 
        - If recipient is online, server checks their status with `client_alive()`.
            - If recipient is not responsive, the server saves the message and updates and broadcasts its table.
            - If recipient is reponsive, the server does NOT save the message. It notifies the client of this by sending a message with header `save` and `ERR` in the body. Then, it sends the client table to the client so it can update its local copy.
    - `save_msg(recipient, sender, msg, channel=False)`
        - Saves messages with dictionary `saved` which stores messages in the format `{<name> : [<formatted msg>, ...]}`
        - Formats messages to include sender, timestamp, and message body. "Channel-Message" is prepended if channel=True.
    - `client_alive(addr)` 
        - Sends an ACK with header `hello` and returns True if it receives an ACK back within 500ms. Returns False otherwise.
        - Timeout implemented with `time.time()`, a while loop checking if class attributed `acked` has been flipped to True. This occurs when the server receives an ACK back from the client with header `hello`.
- Forwarding saved messages
    - Server calls `send_saved()` while registering a cilent if the client is a returning user.
    - `send_saved(addr, name)` 
        - If `name` is in the dictionary of saved messages `saved`, then the server sends each of the saved messages one at a time with the header "saved" to `addr`. 
        - The sequence of messages are preceded with a message with header "saved" and content `\t`, and succeeded similarly with a message with content `\n`. This is to notify the client of the start/end of saved messages it will be receiving.

#### Group Chat
- Initiated by a client message with header `all` by calling `send_all()`. 
- `send_all(addr, data)`
    - Data includes sender and message, split by `\n`.
    - If the message is not an ACK, the message is broadcasted to all clients with `broadcast_msg()`.
    - If the message is an ACK, then the sender has received a channel message forwarded by the server. To note this, the server changes the boolean value of the sender in the dictionary `channel_acks` to True.
- `broadcast_msg(addr, sender, msg)`
    - Sends an ACK to the sender with header `all` (to `addr`).
    - Outgoing message takes the following format: `"all\n<sender>\n<content>`
    - Attempts to send message to all clients except the sender. Saves message for offline recipients and sends messages to online recipients. Online recipients are saved as keys in a dictionary `channel_acks` with initial value False.
    - After broadcasting to all clients, the server starts an instance of Python's Timer class which starts a thread that calls `check_channel()` in 500 ms to see if all online recipients have ACKed the channel message. 
- `check_channel(sender, msg)`
    - Checks if the values for all clients in the dictionary `channel_acks` are True.
    - If not True, the server checks if the client is still responsive with `client_alive()` and updates the table accordingly. The table is broadcasted if there are any updates.


### `client.py`

Defines a Client class which is created in client mode by `Chatapp.py`.

#### Initialization
- `run()` is called on a Client object in `ChatApp.py`. 
    - This binds the client socket to the client port
    - Starts a thread that runs `recv()` for receiving messages
    - Registers the client with `register()`
    - Calls `process_input()` to processing user input.
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

#### Register
- Initiated by `run()` when the client is first started or by user input starting with `>>> reg ...`
    - If the remainder of the input matches the client's name and the client is not online (stored as class attributes), the client calls `register()`.
    - If the client is already online or is trying to register with a different name, the prompt notifies the user and registration terminates.
- `register()`
    - Sends server registration request with `reg` header and client name in body.
    - Waits up to 500ms to receive a broadcasted table from the server which indicates successful registration.
- If the client receives a message from the server with header `reg` and "ERR" in the body, then the client name has already been taken by another user. The program quits so the user can start a client with a different name.

#### Deregister
- Initiated by user input starting with `>>> dereg ...`
    - If the rest of the input matches the users name and the user is currently online, the Client calls `deregister()`.
    - Otherwise, the user is notified that the client is already offline or that it can only register with its own name and deregistration terminates.
- `deregister()`
    - Attempts to send dereg request to server up to 5 times. An attempt times out if an ACK isn't received in 500ms. 
    - Timeout was implemented with `time.time()` and a loop checking the boolean class attribute `acked` which is flipped to True if the client receives an ACK with header `dereg`.

#### Direct Chat
- Sending messages
    - Initiated by user input starting with `>>> send ...`. If name and message (length <= 2000 chars) are both in input, calls `send(name, msg)`. Otherwise, prints error message and aborts send.
    - `send(name, msg)`
        - If `name` found in client table and the associated status is online, the client sends `msg` with the header "msg" to the address associated with `name`.
            - If an ACK with header "msg" from the destination address is received within 500ms, client displays a prompt that the message was received.
            - If no ACK was received, the client displays a prompt that the message was not ACKed and calls `send_offline(msg)` to send `msg` to the server (next section).
            - Timeout implemented in the same way as in `deregister()`.
        - If `name` found in client table and the associated status is offine, calls `send_offline(msg)`.

- Receiving messages
    - Messages coming from addresses different from the server address are all treated as client messages by calling `recv_client(buf, addr)`, where `buf` includes the header and message.
    - `recv_client(buf, addr)`
        - If the header is "msg", then the sock sends a message with header "ack" back to `addr` and prints the sender and recipient.
        - If the header is "ack" and `addr` matches the address of the message destination, the class attribute `acked` is flipped to True to cancel the timeout.
    
#### Offline messages
- Sending offline messages: 
    - Initiated when (1) The recipient is not online according to the client table, or (2) Sending a direct chat times out by calling `send_offline()`
    - `send_offline(msg)`
        - Sends message to server with header `save` and body format: `<sender name>\n<msg>`. 
        - Attempts to send save request up to 5 times, each waiting 500ms for an ACK from the server with header `save`.
        - Timeout implemented the same way as in `deregister()`.

- Receiving offline messages
    - Upon returning online with `reg`, the server will send all the messages saved for the client one message at a time (including sender, timestamp, and message), each with the header `saved`.
    - The start of the sequence of saved messages is communicated by the server with message with header `saved` and message body `\t`. The end is communicated similarly with message body `\n`. This allows the client to display all saved messages in a row without being interrupted by other prompts or functions.

#### Group Chat
- Sending channel messages
    - Initiated by user input starting with `>>> send_all <message>`. If message is 2000 chars or less, calls `send_all()`.
    - `send_all()`
        - Sends a message in the format `all\n<client name>\n<msg>` to the server.
        - Attempts to send send_all request up to 5 times, each waiting 500ms for an ACK from the server with header `all`. Timeout implemented in the same way as for deregister.
        - After 5 failed attempts, the client notifies the user with an error message.

- Receiving channel messages
    - All channel messages are received through the server and have the header `all`. 
    - If the message content is an ACK, then the class attribute `acked` is flipped to True, informing `send_all()` of success and stopping any further attempts to contact the server.
    - Otherwise, the content is an incoming channel with format `<sender>\n<msg>`. 
        - The client displays the message in the format `[Channel-Message <sender>: <msg>]`. 
        - Then, it responds to the server with an ack with an ACK format `all\n<client name>\nACK` so the server doesn't need to search through its client table to find the name associated with the address that sent the ACK.

## Tests

I tested all the required functionalities and error catching to the best of my ablities, and I have not found any bugs. 

The text output for tests are provided in the specs are provided in `test.txt`. Tests 1-3 are the outputs for the 3 test cases provided in the specs.

*Test 4: Stored messages for direct and group chats to an offline client.*
- Start server
- Start client x
- Start client y
- Start client z 
- dereg y
- send_all by x
- send z -> y
- reg y

*Test 5: Detecting silent leave via `send_all`.*
- Start server
- Start client x
- Start client y
- Start client z 
- Silent leave by x
- send_all by y (server doesn't get an ack from x, updates table and broadcasts)



