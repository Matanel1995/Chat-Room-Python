# Chat-Room-Python

Chat room Python implemented

## Client Instructions

**The client can run *only* after the server is already running!**

### Connecting to the server
    Run the 'client' program.
### Disconnecting from the server
    Send the message 'disconnect'
### Sending a text message
    Typing any message that isn't a code word (Case Sensitive!)
    OK examples:
    'Disconnect'
    'udp is cool'
***Code Words:***
* 'disconnect'
* 'UDP'
* 'set_msg_all'
* 'set_msg'
### Sending a text message to a SPECIFIC participant
    Type '#' and the nickname of the participant you wish to send the message to.
    for example- if the nickname is 'Amit' and the private message is 'hello Amit':
            we write '#Amit hello Amit'
### Setting a PRIVATE chat with a specific participant
    Type 'set_msg' and the nickname of the participent you wish to contact.
    For example- to privately send messages to 'Amit', we write 'set_msgAmit'
 ### Setting the chat to PUBLIC (all participants)
    Type 'set_msg_all'
### Getting a list of all online participants
    Type 'get_users'

### Getting a list of all the files on the server
    Type 'get_list_file'
### Sending a request to download a file from the server
### Download a file from the server
