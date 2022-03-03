import socket
import threading
from udprclient import UdprClient


class Client:

    def __init__(self):
        self.bufferSize = 1024
        self.to_user = ''  # USe for specific message to user
        self.client = socket.socket(socket.AF_INET, socket.SOCK_STREAM)  # socket TCP AF_INET - IPv4 , SOCK_STREAM - TCP
        self.nickname = ''
        self.client_udp = None  # To store UDP socket when needed
        self.port_tuple = None  # ports for UDP

# Listening to Server and Sending Nickname
    def receive(self):
        while True:
            try:
                # Receive Message From Server
                # If 'NICK' Send Nickname
                message = self.client.recv(self.bufferSize).decode('utf-8')
                if message == 'NICK':
                    self.client.send(self.nickname.encode('utf-8'))
                elif message == 'NICK_TAKEN':
                    print('Choose other nickname (previous one already taken): ')
                    nickname = input()
                    self.client.send(nickname.encode('utf-8'))
                elif message == 'You have been disconnected':
                    print(message)
                    break
                elif message == 'GOT_IT' or message == 'GOT_ITa joined!Connected to server!':  # If the username is ok
                    self.start_write()
                elif message.split(":")[0] == 'ports':
                    self.port_tuple = (int(message.split(":")[1]), int(message.split(":")[2]))
                    # Create reliable UDP object and start the thread
                    self.client_udp = UdprClient(self.nickname, self.port_tuple)
                    self.client_udp.start()
                    self.client_udp.join()
                else:
                    print(message)
            except:
                # Close Connection When Error
                print("An error occurred!")
                self.client.close()
                break

    # Sending Messages To Server
    def write(self):
        while True:
            message = '{}: {}'.format(self.nickname, input(''))
            temp = message.split(" ")
            # Nothing in message so we don't do anything
            if temp[0] == '' or temp[1] == '':
                continue
            # If the user ask to disconnect
            if temp[1] == 'disconnect':
                self.client.send(message.encode('utf-8'))
                exit(1)
            # If the user ask to download a file
            elif temp[1] == 'download_file':
                self.client.send(message.encode('utf-8'))
                continue
            # If the user want to send message to all users
            elif (len(temp[1]) >= 11) & (temp[1][:11] == 'set_msg_all'):
                self.to_user = ''
            # If the user ask to send message to specific user we set message to specific client
            elif (len(temp[1]) >= 7) & (temp[1][:7] == 'set_msg'):
                self.to_user = temp[1][7:]
            # sending the message to the server
            else:
                # adding message information if its to specific user and sent the message
                if self.to_user != '':
                    temp = message.split(" ")
                    temp.insert(1, '#' + self.to_user)
                    glue = ' '
                    message = glue.join(temp)
                self.client.send(message.encode('utf-8'))

    def start_write(self):
        # Start threads for writing
        write_thread = threading.Thread(target=self.write)
        write_thread.start()

    def start_recive(self):
        # Connect to server and starting Threads For Listening
        self.client.connect(('127.0.0.1', 55000))
        self.nickname = input("Choose your nickname: ")
        receive_thread = threading.Thread(target=self.receive)
        receive_thread.start()


if __name__ == "__main__":

    print("*** WAIT UNTIL YOU SEE YOU ARE CONNECTED AND THEN YOU CAN START USE THE CHAT ***")
    print("(1) To send message to all other user just type your message and they will get it.")
    print("(2) To send private message write in this format ---send_msg{some other user}-- and then the message.")
    print("(3) To send message to all users write in this format ---set_msg_all---.")
    print("(4) To get the file names just type ---get_list_file---.")
    print("(5): To get all user names type ---get_users---.")
    print("(6): To download_file type ---download_file {some file name} example download_file a.txt.")
    print("(7): That it just have fun!!!!.")
    my_client = Client()
    my_client.start_recive()

