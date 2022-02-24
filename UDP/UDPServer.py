import math
import threading

from tclient import Client2
import socket
import time
import os
import sys


class Server:
    max_packet_size = 2 ** 16
    time_out = 0.01  # should do better
    fragment_size = 500
    seq_max = 10
    window_size = 5
    time_start = time.time()

    def __init__(self) -> None:
        self.server_sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.server_sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        self.server_sock_udp = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        # self.server_sock_udp.setblocking(False)
        self.server_sock_udp.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        self.server_sock.bind(('127.0.0.1', 55000))
        self.server_sock_udp.bind(('127.0.0.1', 55002))
        self.server_sock.listen(5)
        self.clients_map = {}
        self.buffer_data = {}
        self.ack_data = {}
        self.clients_map_udp = {}
        self.file_names = []
        self.ports = [0 for i in range(0, 15)]

    def send_files(self, nick_name):
        for i in self.file_names:
            self.clients_map.get(nick_name).client_sock.send(i.encode('utf-8'))

    def three_way_size(self, nick_name, file_name, to_send):
        try:
            self.server_sock_udp.settimeout(self.time_out)
            message, _ = self.server_sock_udp.recvfrom(1024)
            real_message = message.decode('utf-8')
            if real_message == 'GIVE_SIZE':
                print(to_send)
                self.server_sock_udp.sendto(to_send.encode('utf-8'), ('127.0.0.1', self.clients_map_udp.get(nick_name)))
                msg, _ = self.server_sock_udp.recvfrom(1024)
                if msg.decode('utf-8') == 'ACK':
                    self.server_sock_udp.settimeout(None)
                    return True
                else:
                    self.three_way_size(nick_name, file_name, to_send)
        except:
            self.three_way_size(nick_name, file_name, to_send)

    def three_way_handshake(self, nick_name, counter, syn_received):
        try:
            self.server_sock_udp.settimeout(self.time_out)
            message, _ = self.server_sock_udp.recvfrom(self.max_packet_size)
            print(message)
            if message.decode('utf-8') == 'SYN' or syn_received:
                syn_received = True
                self.server_sock_udp.sendto('ACK'.encode('utf-8'), ('127.0.0.1', self.clients_map_udp.get(nick_name)))
                ans, _ = self.server_sock_udp.recvfrom(self.max_packet_size)
                if ans.decode('utf-8') == 'ACK':
                    self.server_sock_udp.settimeout(None)
                    print("CONNECTED")
                    return True
            else:
                return False
        except:
            if counter <= 3:
                counter += 0
                self.three_way_handshake(nick_name, counter, syn_received)
            else:
                print("Cannot connect try again")
                return False

    def three_way_finish(self, nick_name):
        try:
            self.server_sock_udp.settimeout(self.time_out)
            self.server_sock_udp.sendto('ACK'.encode('utf-8'),
                                        ('127.0.0.1', self.clients_map_udp.get(nick_name)))
            ans, _ = self.server_sock_udp.recvfrom(self.max_packet_size)
            if ans.decode('utf-8') == 'ACK':
                self.server_sock_udp.settimeout(None)
                return True
            else:
                self.three_way_finish(nick_name)
        except:
            self.three_way_finish(nick_name)

    def check_ack(self, nack, start_index, end_index, time_started, nick_name):
        while True:
            try:
                ack, _ = self.server_sock_udp.recvfrom(1024)
                if ack.decode() == 'FINISHED_FILE':
                    self.three_way_finish(nick_name)
                    return 0
                for i in range(start_index, end_index):
                    if i % 10 == int(ack.decode('utf-8')) % 10:
                        nack[i] = 1
                        return 1
            except:
                break

    def find_start_end(self, nack):
        for i in range(0, len(nack)):
            if nack[i] == 0:
                start_index = i
                end_index = min(i + self.window_size, len(nack) - 1)
                return start_index, end_index

    def sliding_window(self, nick_name, file_name):
        start_index = 0
        end_index = 0
        bol = True
        bol1 = True
        finished = True
        nack_packet = [0 for i in range(0, len(self.buffer_data.get(nick_name).get(file_name)))]
        packet_number_help_me = 0
        bool_percent = True
        while end_index <= len(nack_packet):
            for i in range(len(nack_packet) - self.window_size, len(nack_packet)):
                # if start_index >= len(nack_packet) - self.window_size-1 and nack_packet[start_index+i] == 0:
                #     finished = False
                if nack_packet[i] == 0:
                    finished = False
            if finished:
                print("FINISHED")
                break
            start_index, end_index = self.find_start_end(nack_packet)
            if start_index == 0 and end_index == 0:
                break
            for k in range(start_index, end_index):
                if nack_packet[k] == 0:
                    data = self.buffer_data.get(nick_name).get(file_name)[k]
                    ind = (k % self.seq_max).to_bytes(1, byteorder='big')
                    packet_number_help_me += 1
                    packet = ind + data
                    time_sent = time.time()
                    self.server_sock_udp.sendto(packet, ('127.0.0.1', self.clients_map_udp.get(nick_name)))
            self.server_sock_udp.settimeout(self.time_out)
            percent = (start_index / len(nack_packet)) * 100
            if bool_percent and 51 > percent > 49:
                bool_percent = False
                print("Need to send now confirm proceed")
                while True:
                    try:
                        self.server_sock_udp.sendto('CONFIRM_PROCEED'.encode('utf-8'),
                                                    ('127.0.0.1', self.clients_map_udp.get(nick_name)))
                        msg, _ = self.server_sock_udp.recvfrom(1024)
                        if msg.decode('utf-8') == 'PROCEED':
                            break
                        elif msg.decode('utf-8') == 'NO_PROCEED':
                            end_index = len(nack_packet) + 1
                            break
                        else:
                            continue
                    except:
                        continue
            percent = "{:.2f}".format(percent)
            print(f'Send {percent}% from the file!')
            if self.check_ack(nack_packet, start_index, end_index, time_sent, nick_name) == 0:
                print("File transferred")
                break

    def update_buffer(self, nick_name, file_name, segment_size):
        with open(file_name, 'rb') as f:
            j = 0
            while j <= segment_size:
                data = f.read(self.fragment_size)
                self.buffer_data.get(nick_name).get(file_name).append(data)
                j += 1

    def udp_transfer_files(self, nick_name, file_name):
        bol = False
        bol_2 = True
        file_size = os.path.getsize(file_name)
        segment_size = math.ceil(file_size / self.fragment_size)
        # sis = math.ceil(file_size/self.fragment_size)%self.window_size
        # segment_size = segment_size+self.window_size-sis
        # print(segment_size,sis)
        if self.buffer_data.get(nick_name) is None:
            self.buffer_data[nick_name] = {}
            self.buffer_data.get(nick_name)[file_name] = []
        if self.buffer_data.get(nick_name) is not None:
            if self.buffer_data.get(nick_name).get(file_name) is None:
                self.buffer_data.get(nick_name)[file_name] = []

        if self.clients_map_udp.get(nick_name) is None:
            for i in range(0, 15):
                if self.ports[i] == 0:
                    self.clients_map_udp[nick_name] = 55003 + i
                    self.ports[i] = 1
                    bol = True
                    self.sent_to_other_user(nick_name,
                                            f'listen to port {self.clients_map_udp.get(nick_name)}'.encode('utf-8'))
                    break
        if bol:
            bol_2 = self.three_way_handshake(nick_name, 0, False)
            # if bol_2 is False:
            # # self.clients_map_udp.pop(nick_name)
            bol = bol_2
        if bol_2 or bol:
            to_send = 'SIZE:' + str(segment_size)
            self.three_way_size(nick_name, file_name, to_send)
            # self.server_sock_udp.settimeout(self.time_out)
            # booleean = 'G'
            # while booleean != 'GOT_SIZE':
            #     try:
            #         #print("TRY TO SEND SIZE")
            #         self.server_sock_udp.sendto(to_send.encode('utf-8'),
            #         ('127.0.0.1', self.clients_map_udp.get(nick_name)))
            #         m, _ = self.server_sock_udp.recvfrom(1024)
            #         booleean = m.decode()
            #         print(m.decode())
            #         #MAYBE SHOULD ADD TIMEOUT
            #         if m.decode('utf-8') == 'GOT_SIZE':
            #             self.server_sock_udp.sendto('ACK'.encode('utf-8'),
            #             ('127.0.0.1', self.clients_map_udp.get(nick_name)))
            #     except:
            #         continue

            self.update_buffer(nick_name, file_name, segment_size)
            self.sliding_window(nick_name, file_name)
            self.server_sock_udp.sendto('s'.encode('utf-8'), ('127.0.0.1', self.clients_map_udp.get(nick_name)))

    def broadcast(self, message, nick_name):
        for nick, client in self.clients_map.items():
            if nick != nick_name:
                client.client_sock.send(message)

    def send_users(self, nick_name):
        for nick in self.clients_map:
            if nick != nick_name:
                self.clients_map[nick_name].client_sock.send(nick.encode('utf-8'))

    def sent_to_other_user(self, receiver, message_to):
        self.clients_map.get(receiver).client_sock.send(message_to)

    def handle_messages(self, nick_name):
        while True:
            try:
                bool_ = False
                message = self.clients_map[nick_name].client_sock.recv(1024).decode('utf-8')
                print(message)

                if message == f'{nick_name}: exit':
                    self.broadcast(f'{nick_name} has left the chat room'.encode('utf-8'), nick_name)
                    self.clients_map.get(nick_name).client_sock.send('Goodbye'.encode('utf-8'))
                    self.clients_map.pop(nick_name)
                    if self.clients_map_udp.get(nick_name) is not None:
                        self.server_sock_udp.sendto('EXIT'.encode('utf-8'),
                                                    ('127.0.0.1', self.clients_map_udp.get(nick_name)))
                        self.ports[self.clients_map_udp.get(nick_name) - 50003] = 0
                    break
                pure_message = message.split(": ")
                file_message = message.split(" ")
                send_to_message = str(pure_message).split("_")
                print(len(pure_message))
                if len(file_message) >= 3 and file_message[1] == "download_file":
                    file_name = file_message[2]
                    if file_name in self.file_names:
                        download_thread = threading.Thread(target=self.udp_transfer_files, args=(nick_name, file_name))
                        download_thread.start()

                    else:
                        self.sent_to_other_user(nick_name, 'there is no such a file with that name'.encode('utf-8'))
                elif message == f'{nick_name}: get_file_names':
                    self.send_files(nick_name)
                elif pure_message[1] == "get_user_names":
                    self.send_users(nick_name)
                elif len(send_to_message) >= 3:
                    meta = send_to_message[0].split(",")
                    # print(meta[1])
                    met_meta = meta[1][2:len(meta[1])]
                    print(met_meta)
                    print(send_to_message[1])
                    if met_meta == "send" and send_to_message[1] == "to":
                        print("inside")
                        meta_receiver = send_to_message[2].split()
                        receiver = meta_receiver[0]
                        print(receiver)
                        if self.clients_map.get(receiver) is not None:
                            message_to = '' + str(nick_name) + ":" + str(
                                send_to_message[2][len(receiver):len(send_to_message[2]) - 2])
                            self.sent_to_other_user(receiver, message_to.encode())
                        else:
                            self.sent_to_other_user(nick_name, f'{receiver} isn\'t in the room anymore'.encode('utf-8'))
                elif self.clients_map.get(nick_name) is not None:
                    self.broadcast(message.encode('utf-8'), nick_name)
                # else:
                #     self.broadcast(message.encode('utf-8'), nick_name)

            except:
                self.clients_map[nick_name].close()
                self.clients_map.pop(nick_name)
                break

    def receive(self):
        while True:
            print('Server is running and listening')
            client, address = self.server_sock.accept()
            new_client = Client2()
            new_client.client_sock = client
            print(f'connection establish with {str(address)}')
            client.send('nick?'.encode('utf-8'))
            nick_name = client.recv(1024).decode('utf-8')
            while self.clients_map.get(nick_name) is not None:
                client.send('choose another nick'.encode('utf-8'))
                nick_name = client.recv(1024).decode('utf-8')
                print(nick_name)
            new_client.nick_name = nick_name
            # self.clients_map[nick_name] = client
            self.clients_map[nick_name] = new_client
            print(f' The nick_name of this client is {nick_name}')
            self.broadcast(f'{nick_name} has connected to the room'.encode('utf-8'), nick_name)
            client.send('you are connected'.encode('utf-8'))
            print(nick_name)
            tread = threading.Thread(target=self.handle_messages, args=(nick_name,))
            tread.start()


if __name__ == "__main__":
    server = Server()
    server.file_names.append("test.txt")
    server.file_names.append("another.txt")
    host_name = socket.gethostname()
    print(socket.gethostbyaddr(host_name))
    my_ip = socket.gethostbyname(host_name)
    print(my_ip)
    server.receive()
