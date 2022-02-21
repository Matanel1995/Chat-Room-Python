import socket
import threading
import time

#connection data
host = '127.0.0.1'
port = 55000

# Starting Server
server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
server.bind((host, port))
server.listen()


# Lists For Clients and Their Nicknames
clients = []
nicknames = []
c_address = []


def is_specific(message):
    message = message.decode('utf-8')
    temp = message.split(" ")
    if temp[1][0] == '#':
        for nickname in nicknames:
            if nickname == temp[1][1:]:
                return nickname
    return None


# Sending Messages To All Connected Clients
def broadcast(message):
    specific = is_specific(message)
    if specific is None:
        for client in clients:
            client.send(message)
    else:
        temp_string = '#'+specific
        client = clients[nicknames.index(specific)]
        # decoding message so i can modify it
        message = message.decode('utf-8')

        # removing unnecessary chars from the string
        message = message.replace(temp_string , "")
        message = message.replace("  ", " ")
        message = "(private) " + message

        # encode the message so i can send it
        message = message.encode('utf-8')
        client.send(message)


""" 
Handling Messages From Clients
Check the request from the client and response accordingly
possible requests:
    1. Send message to all users or specific user in chat room.
    2. Get all the users in chat room.
    3. Get list of all files in room server
    4. Get file from the server (Reliable UDP)
"""


def handle(client):
    while True:
        try:
            # decode message to know how to handle
            message = client.recv(1024)
            message = message.decode('utf-8')
            temp = message.split(" ")
            print(temp[1] + '\n')
            # If the user want to get all the users in chat room
            if temp[1] == 'get_users':
                response_message = '----- Users in char room -------\n'
                for i in range(0, len(nicknames)):
                    response_message += '(' + str(i+1) + ') ' + str(nicknames[i]) + '\n'
                response_message += '---------- Thats all! ----------'
                response_message = response_message.encode('utf-8')
                client.send(response_message)
            # If the user want to disconnect
            elif temp[1] == 'disconnect':
                remove_from_server(client)
                break
            elif temp[1] == 'UDP':
                client_addr = (str(temp[2][1:-2]), int(temp[3]))
                print("in elif = " + str(client_addr))
                thread = threading.Thread(target=send_udp, args=(client_addr,))
                thread.start()
                pass
            # Default option: the user want to send message
            else:
                # Broadcasting Messages
                message = message.encode('utf-8')
                broadcast(message)
        # The user disconnected somehow 
        except:
            # Removing And Closing Clients
            remove_from_server(client)
            break


# Receiving / Listening Function
def receive():
    while True:
        # Accept Connection
        client, address = server.accept()
        print("Connected with {}".format(str(address)))

        # Request And Store Nickname
        client.send('NICK'.encode('utf-8'))
        nickname = client.recv(1024).decode('utf-8')
        nicknames.append(nickname)
        clients.append(client)
        c_address.append(address)

        # Print And Broadcast Nickname
        print("Nickname is {}".format(nickname))
        broadcast("{} joined!".format(nickname).encode('utf-8'))
        client.send('Connected to server!'.encode('utf-8'))

        # Start Handling Thread For Client
        thread = threading.Thread(target=handle, args=(client,))
        thread.start()


def remove_from_server(client):
    # Removing And Closing Clients
    response_message = 'You have been disconnected'
    response_message = response_message.encode('utf-8')
    client.send(response_message)
    # time.sleep(0.1)
    # index = clients.index(client)
    # clients.remove(client)
    # client.close()
    # nickname = nicknames[index]
    # broadcast('{} left!'.format(nickname).encode('utf-8'))
    # nicknames.remove(nickname)


def send_udp(address):
    message = "This is udp message"
    message = message.encode('utf-8')
    udp_socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    udp_socket.bind(('127.0.0.1',55001))
    udp_socket.sendto(message,address)


print('Welcome to The Chat room\n '
      '##### If you want to send message to specific client use "#" before his nickname!!\n '
      'For example #Client <here your massage>\n Enjoy chating!\n')
receive()
