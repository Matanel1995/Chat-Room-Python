# Chat-Room-Python

In this project we implemnted a chat room using python.
Clients can connect to the room send a recive messages to all other clients or to a specific client.
Also clients can download files from the server using our new reliable UDP protocol.

# Reliable UDP
We implemented a new reliable UDP protocol baset on the selective repeat algorithm.</br>
We divide our file into parts and give each part a sequnce number between 0 to 9 (modulo 10).</br>
For each part the server send to the client, the client will response with ACK (the seq number he got).</br>
When the server recive an ACK from the client he marks that specific packet so he will know not to send it again.</br>
If the packet wasnt marked the server will send it again until he will get an ACK.</br></br>



## Client Instructions

**The client can run *only* after the server is already running!**
The client have number of code words he can use:</br>
* 'disconnect' - For disconnecting.
* 'get_users' - Get a list with all users in the chat room.
* 'set_msg_all' - Next messages will be send to all users.
* 'set_msg' - Next message will be send only to a specific user
* 'get_list_file' - Get a list with all the file in the server you can download
* 'download_file' - Request to download a file froim the server.

### Connecting to the server

    Run the 'client' program.

### Disconnecting from the server

    Send the message 'disconnect'

### Sending a text message

    Typing any message that isn't a code word (Case Sensitive!)
    OK examples:
    'Disconnect'
    'udp is cool'


### Setting a PRIVATE chat with a specific participant

[//]: # (    Once you've pressed ENTER all your outgoing messages will be sent only to the participant you chose. )

    Type 'set_msg' and the nickname of the participent you wish to contact.
    Remember! Until you set the chat back tou public, all your messages will be sent only to the participant you chose.
    For example- to privately send messages to 'Amit', we write 'set_msgAmit'

### Setting the chat to PUBLIC (all participants)

    Type 'set_msg_all'

### Getting a list of all online participants

    Type 'get_users'

### Getting a list of all the files on the server

    Type 'get_list_file'

### Sending a request to download a file from the server

In order to download a file from the server's file list, type 'download_file' ***add space*** and enter the file name +
file extension.
If successful, after downloading 40% you will be asked to confirm the rest of the download (or not).
Finally, you will be asked to provide the new file name ***+*** file extension.

## Chat room flow chart

![0001](https://user-images.githubusercontent.com/92520981/156567692-102af44b-932c-4289-8626-7fbf7631fe46.jpg)

## How we dealing with latency
At each iteration of sending data we save the time of the first packet that we send </br>
when we recive an ACK for that packet we calculate the RTT (current time - marked time)</br>
with that information we calculate the new estimated RTT using this formula :</br>
EstimatedRTT = (1- a)*EstimatedRTT + a*SampleRTT. </br>
When a = 0.125

## How we dealing with packet loss
* In case packet from the server to the client is lost the client will not send an ACK for that packet, so the server will send it again.</br>
* In case packet from the client to the server was lost(ACK), the server will send again the the data but the client will see he allready got that packet so he will send back ACK automatically 

## UML
![UML](https://user-images.githubusercontent.com/92520981/156637671-ef83094e-9de8-45fc-8ae7-cb2aa4b29705.jpeg)


## Pictures of the chat room
Server on the left client on the right </br></br>
Star of the download until proceed:</br>
![download_1](https://user-images.githubusercontent.com/92520981/156574442-f693c998-cac6-42e8-a929-7e2332f9071b.PNG)

after proceed:</br>
![download_2](https://user-images.githubusercontent.com/92520981/156574539-80c938ec-51d4-41be-8b57-6da98b327b03.PNG)


