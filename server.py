import socket
import threading
import time
from udprserver import UdprServer

#connection data
host = '127.0.0.1'
port = 55000

# Starting Server
server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
server.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
server.bind((host, port))
server_sock_udp = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
server_sock_udp.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
server_sock_udp.bind(('127.0.0.1', 55001))
server.listen()


lock = threading.Lock()


# Lists For Clients and Their Nicknames
clients = []
nicknames = []
c_address = []
ports = [0 for i in range(0, 15)]
ports[0] = 1
ports[1] = 1
# List of all the files in the server
files = ['txt.txt', 'photo.jpeg', 'MP4.mp4']


def is_specific(message):
    message = message.decode('utf-8')
    temp = message.split(" ")
    try:
        if temp[1][0] == '#':
            for nickname in nicknames:
                if nickname == temp[1][1:]:
                    return nickname
                return None
    except:
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
        message = message.replace(temp_string, "")
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
            elif temp[1] == 'get_list_file':
                response_message = '----- File in server -------\n'
                for i in files:
                    response_message += str(i) + '\n'
                response_message += '---------- Thats all! ----------'
                response_message = response_message.encode('utf-8')
                client.send(response_message)
            elif temp[1] == 'download_file':
                print("IN ELIF")
                if temp[2] in files:
                    print("file exist")
                    for i in range(0, 15):
                        if ports[i] == 0:
                            port = 55000 + i
                            ports[i] = 1
                            client.send(f'listen to port {port}'.encode('utf-8'))
                            print(f'send port number to client {port}')
                            break
                    print(server_sock_udp)
                    file_transfer = UdprServer(port, temp[0].strip(":"), temp[2], server_sock_udp, lock)
                    print("created udp instance")
                    file_transfer.start()
                    file_transfer.join()
                    ports[port - 55000] = 0
                else:
                    response_message = "No such file in the server"
                    client.send(response_message.encode('utf-8'))
                # client_addr = (str(temp[2][1:-2]), int(temp[3]))
                # print("in elif = " + str(client_addr))
                # thread = threading.Thread(target=send_udp, args=(client_addr,))
                # thread.start()
            # Default option: the user want to send message
            else:
                # Broadcasting Messages
                message = message.encode('utf-8')
                broadcast(message)
        # The user disconnected somehow 
        except socket.error:
            # Removing And Closing Clients
            print("IM HERE BEFORE DISCONNECTING")
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
        while nickname in nicknames:
            client.send('NICK_TAKEN'.encode('utf-8'))
            nickname = client.recv(1024).decode('utf-8')
        client.send('GOT_IT'.encode('utf-8'))
        time.sleep(0.03)
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
    client_index = clients.index(client)
    clients.pop(client_index)
    nicknames.pop(client_index)
    c_address.pop(client_index)
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
    udp_socket.bind(('127.0.0.1', 55001))
    udp_socket.sendto(message, address)


print('Welcome to The Chat room\n '
      '##### If you want to send message to specific client use "#" before his nickname!!\n '
      'For example #Client <here your massage>\n Enjoy chating!\n')
receive()
