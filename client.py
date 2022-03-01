import socket
import threading
from udprclient import UdprClient

bufferSize = 1024

to_user = ''

# Choosing Nickname
nickname = input("Choose your nickname: ")
print("*** WAIT UNTIL YOU SEE YOU ARE CONNECTED AND THEN YOU CAN START USE THE CHAT ***")
print("(1) To send message to all other user just type your message and they will get it.")
print("(2) To send private message write in this format ---send_to_{some other user}-- and then the message.")
print("(3) To get the file names just type ---get_file_names---.")
print("(4): To get all user names type ---get_user_names---.")
print("(5): To download_file type ---download_file {some file name} example download_file a.txt.")
print("(6): That it just have fun!!!!.")

# Connecting To Server
client = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
client.connect(('127.0.0.1', 55000))


# Listening to Server and Sending Nickname
def receive():
    global nickname
    while True:
        try:
            # Receive Message From Server
            # If 'NICK' Send Nickname
            message = client.recv(bufferSize).decode('utf-8')
            if message == 'NICK':
                client.send(nickname.encode('utf-8'))
            elif message == 'NICK_TAKEN':
                print('Choose other nickname (previous one already taken): ')
                nickname = input()
                print(nickname)
                client.send(nickname.encode('utf-8'))
            elif message == 'You have been disconnected':
                print(message)
                break
            elif message == 'GOT_IT' or message == 'GOT_ITa joined!Connected to server!':
                start_write()
            else:
                print(message)
        except:
            # Close Connection When Error
            print("An error occurred!")
            client.close()
            break


def receive_udp(udp_socket):
    while True:
        try:
            # Receive Message From Server
            message, addr = udp_socket.recvfrom(bufferSize)
            message = message.decode('utf-8')
            print(message)
        except udp_socket.error as e:
            # Close Connection When Error
            print("An error occurred!" + e)
            udp_socket.close()
            break


# Sending Messages To Server
def write():
    global to_user
    while True:
        message = '{}: {}'.format(nickname, input(''))
        print(message)
        temp = message.split(" ")
        # Nothing in message so we don't do anything
        if temp[0] == '' or temp[1] == '':
            continue
        # If the user ask to disconnect
        if temp[1] == 'disconnect':
            client.send(message.encode('utf-8'))
            exit(1)
        # If the user ask to download a file
        elif temp[1] == 'download_file':
            client.send(message.encode('utf-8'))

            # Get the ports i need to listen and sent my file to
            port_tuple_list = client.recv(bufferSize).decode('utf-8').split(":")
            port_tuple = (int(port_tuple_list[0]), int(port_tuple_list[1]))

            # Create reliable UDP object and start the thread
            client_udp = UdprClient(nickname, port_tuple)
            client_udp.start()
            client_udp.join()
            continue
        # If the user want to send message to all users
        elif (len(temp[1]) >= 11) & (temp[1][:11] == 'set_msg_all'):
            to_user = ''
        # If the user ask to send message to specific user we set message to specific client
        elif (len(temp[1]) >= 7) & (temp[1][:7] == 'set_msg'):
            to_user = temp[1][7:]
        # sending the message to the server
        else:
            # adding message information if its to specific user and sent the message
            if to_user != '':
                temp = message.split(" ")
                temp.insert(1, '#' + to_user)
                glue = ' '
                message = glue.join(temp)
            client.send(message.encode('utf-8'))


def start_write():
    # Start threads for writing
    write_thread = threading.Thread(target=write)
    write_thread.start()


# Starting Threads For Listening
receive_thread = threading.Thread(target=receive)
receive_thread.start()

