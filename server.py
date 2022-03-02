import socket
import threading
import time
from udprserver import UdprServer


class Server:

    def __init__(self):
        # connection data
        self.host = ('127.0.0.1', 55000)
        self.server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.server.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        self.server.bind(self.host)
        self.server.listen()
        # Lists For Clients and their Nicknames and the addresses
        self.clients = []
        self.nicknames = []
        self.c_address = []
        self.ports = [0 for i in range(0, 15)]
        self.ports[0] = 1
        # List of all the files in the server
        self.files = ['txt.txt', 'photo.jpeg', 'MP4.mp4']

    def is_specific(self, message):
        """Function to deal with specific messages"""
        message = message.decode('utf-8')
        temp = message.split(" ")
        try:
            if temp[1][0] == '#':
                for nickname in self.nicknames:
                    if nickname == temp[1][1:]:
                        return nickname
                    return None
        except:
            return None


    def broadcast(self,message):
        """Function to broadcast the message it received from the client to all users
            Unless the message is for specific client"""
        specific = self.is_specific(message)
        if specific is None:
            for client in self.clients:
                client.send(message)
        else:
            temp_string = '#'+specific
            client = self.clients[self.nicknames.index(specific)]
            # decoding message so i can modify it
            message = message.decode('utf-8')

            # removing unnecessary chars from the string
            message = message.replace(temp_string, "")
            message = message.replace("  ", " ")
            message = "(private) " + message

            # encode the message so i can send it
            message = message.encode('utf-8')
            client.send(message)


    def handle(self, client):
        """
        Handling Messages From Clients
        Check the request from the client and response accordingly
        possible requests:
            1. Send message to all users or specific user in chat room.
            2. Get all the users in chat room.
            3. Get list of all files in room server
            4. Get file from the server (Reliable UDP)
        """
        while True:
            try:
                # decode message to know how to handle
                message = client.recv(1024)
                message = message.decode('utf-8')
                temp = message.split(" ")
                # If the user want to get all the users in chat room
                if temp[1] == 'get_users':
                    response_message = '----- Users in char room -------\n'
                    for i in range(0, len(self.nicknames)):
                        response_message += '(' + str(i+1) + ') ' + str(self.nicknames[i]) + '\n'
                    response_message += '---------- Thats all! ----------'
                    response_message = response_message.encode('utf-8')
                    client.send(response_message)
                # If the user want to disconnect
                elif temp[1] == 'disconnect':
                    self.remove_from_server(client)
                    break
                # If the user want to get all the files names in the server
                elif temp[1] == 'get_list_file':
                    response_message = '----- File in server -------\n'
                    for i in self.files:
                        response_message += str(i) + '\n'
                    response_message += "---------- That's all! ----------"
                    response_message = response_message.encode('utf-8')
                    client.send(response_message)
                # If user want to download a file from the server
                elif temp[1] == 'download_file':
                    # Check if file exist by name
                    if temp[2] in self.files:
                        print("file exist")
                        # Find free port in range of 55000 - 55015 for server UDP socket
                        for i in range(0, 15):
                            if self.ports[i] == 0:
                                client_port = 55000 + i
                                self.ports[i] = 1
                                break
                        # Find free port in range of 55000 - 55015 for client UDP socket
                        for i in range(0, 15):
                            if self.ports[i] == 0:
                                server_port = 55000 + i
                                self.ports[i] = 1
                                break
                        port_tuple = (server_port, client_port)

                        # Sent the port to the client so he will know how to set up
                        client.send(f'ports:{server_port}:{client_port}'.encode('utf-8'))

                        # Creating reliable UDP Client object and start the threads
                        file_transfer = UdprServer(port_tuple, temp[0].strip(":"), temp[2])
                        file_transfer.start()
                        file_transfer.join()

                        # After we are done with file we clear the port so other client can use them
                        self.ports[server_port - 55000] = 0
                        self.ports[client_port - 55000] = 0
                        continue

                    # File is not in the server so we sent message accordingly
                    else:
                        response_message = "No such file in the server"
                        client.send(response_message.encode('utf-8'))
                        continue

                # Default option: the user want to send message
                else:
                    # Broadcasting Messages
                    print(message)
                    message = message.encode('utf-8')
                    self.broadcast(message)

            # The user disconnected somehow
            except socket.error:
                # Removing And Closing Clients
                self.remove_from_server(client)
                break

    def receive(self):
        """Function to ask the user of his username and check if its already taken
        if its taken we send message to ask for it again
        if the username is free we will start the handle thread"""
        while True:
            # Accept Connection
            client, address = self.server.accept()
            print("Connected with {}".format(str(address)))

            # Request And Store Nickname
            client.send('NICK'.encode('utf-8'))
            nickname = client.recv(1024).decode('utf-8')
            # Check if the username is taken we send new request and receive new username until the username is free
            while nickname in self.nicknames:
                client.send('NICK_TAKEN'.encode('utf-8'))
                nickname = client.recv(1024).decode('utf-8')
            client.send('GOT_IT'.encode('utf-8'))
            time.sleep(0.03)

            # Add the new user to our lists
            self.nicknames.append(nickname)
            self.clients.append(client)
            self.c_address.append(address)

            # Print And Broadcast Nickname
            print("Nickname is {}".format(nickname))
            self.broadcast("{} joined!".format(nickname).encode('utf-8'))
            client.send('Connected to server!'.encode('utf-8'))

            # Start Handling Thread For Client
            thread = threading.Thread(target=self.handle, args=(client,))
            thread.start()

    def remove_from_server(self, client):
        # Removing And Closing Clients
        response_message = 'You have been disconnected'
        response_message = response_message.encode('utf-8')
        client.send(response_message)
        # Find the user index and remove it from all lists
        client_index = self.clients.index(client)
        self.clients.pop(client_index)
        self.nicknames.pop(client_index)
        self.c_address.pop(client_index)


if __name__ == "__main__":
    print('Server is up and running')
    my_server = Server()
    my_server.receive()
