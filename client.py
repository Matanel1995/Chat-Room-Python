import socket
import threading
from udprclient import UdprClient

bufferSize = 1024

to_user = ''

# action = input("In oreder to connect to the server write Connect <ServerIpAddress>\n")
# while(action.split(' ')[0] != 'Connect'):
#     action = input("In oreder to connect to the server write Connect <ServerIpAddress>\n")

# Choosing Nickname
nickname = input("Choose your nickname: ")
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
            elif message == 'GOT_IT':
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
    while True :
        message = '{}: {}'.format(nickname, input(''))
        temp = message.split(" ")
        if temp[0] == '' or temp[1] == '':
            continue
        if temp[1] == 'UDP':
            udp_socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
            udp_socket.bind(("127.0.0.1", 55005))
            message += ' ' + str(udp_socket)[-20:-2]
            client.send(message.encode('utf-8'))
            # Start new thread to receive UDP messages
            receive_udp_thread = threading.Thread(target=receive_udp, args=(udp_socket,))
            receive_udp_thread.start()
            receive_udp_thread.join()
        # Set message to all clients
        if temp[1] == 'disconnect':
            client.send(message.encode('utf-8'))
            exit(1)
        elif temp[1] == 'download_file':
            client.send(message.encode('utf-8'))
            port_num = client.recv(bufferSize).decode('utf-8').split(" ")[3]
            print(f'port number received is {port_num}')
            client_udp = UdprClient(nickname, port_num)
            print("Created UDP instance")
            client_udp.start()
            client_udp.join()
            print("FINISH WITH THREAD")
        elif (len(temp[1]) >= 11) & (temp[1][:11] == 'set_msg_all'):
            to_user = ''
        # Set message to specific client
        elif (len(temp[1]) >= 7) & (temp[1][:7] == 'set_msg'):
            to_user = temp[1][7:]
        else:
            # adding message information if its to specific user and sent the message
            if to_user != '':
                temp = message.split(" ")
                temp.insert(1, '#' + to_user)
                glue = ' '
                message = glue.join(temp)
            client.send(message.encode('utf-8'))

def start_write():
    write_thread = threading.Thread(target=write)
    write_thread.start()

# Starting Threads For Listening And Writing
receive_thread = threading.Thread(target=receive)
receive_thread.start()

