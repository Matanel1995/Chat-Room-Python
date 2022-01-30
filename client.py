import socket
import threading

bufferSize = 1024

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
    while True:
        message = '{}: {}'.format(nickname, input(''))
        temp = message.split(" ")
        if temp[1] == 'UDP':
            udp_socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
            udp_socket.bind(("127.0.0.1",55005))
            message += ' ' + str(udp_socket)[-20:-2]
            client.send(message.encode('utf-8'))
            # Start new thread to receive UDP messages
            receive_udp_thread = threading.Thread(target=receive_udp, args=(udp_socket,))
            receive_udp_thread.start()
        else:
            client.send(message.encode('utf-8'))


# Starting Threads For Listening And Writing
receive_thread = threading.Thread(target=receive)
receive_thread.start()

write_thread = threading.Thread(target=write)
write_thread.start()