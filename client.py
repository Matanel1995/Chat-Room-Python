import socket
import threading

bufferSize = 1024

to_user = ''

# action = input("In order to connect to the server write Connect <ServerIpAddress>\n")
# while(action.split(' ')[0] != 'Connect'):
#     action = input("In order to connect to the server write Connect <ServerIpAddress>\n")

# Choosing Nickname
nickname = input("Choose your nickname: ")

# Connecting To Server
client = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
client.connect(('127.0.0.1', 55000))


# Listening to Server and Sending Nickname
def receive():
    while True:
        try:
            # Receive Message From Server
            # If 'NICK' Send Nickname
            message = client.recv(1024).decode('utf-8')
            if message == 'NICK':
                client.send(nickname.encode('utf-8'))
            elif message == 'You have been disconnected':
                # print(message)
                # client.close()
                client_disconnect()
                break
            else:
                print(message)
        except:
            # Close Connection When Error
            print("An error occurred!")
            # client.close()
            client_disconnect()
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
        temp = message.split(" ")
        if temp[1] == 'UDP':
            udp_socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
            udp_socket.bind(("127.0.0.1", 55005))
            message += ' ' + str(udp_socket)[-20:-2]
            client.send(message.encode('utf-8'))
            # Start new thread to receive UDP messages
            receive_udp_thread = threading.Thread(target=receive_udp, args=(udp_socket,))
            receive_udp_thread.start()
        # Set message to all clients
        if temp[1] == 'disconnect':
            client.send(message.encode('utf-8'))
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


def client_disconnect():
    message = 'You have been disconnected'
    print(message)
    client.close()


# Starting Threads For Listening And Writing
receive_thread = threading.Thread(target=receive)
receive_thread.start()

write_thread = threading.Thread(target=write)
write_thread.start()
