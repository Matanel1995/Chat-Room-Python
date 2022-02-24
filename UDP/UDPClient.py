import sys
import threading
import socket
import time


class Client2(object):
    connected = True
    connected_udp = False
    fragment_size = 500  # in bytes
    window_size = 5
    max_seq_num = 10
    already_connect_udp = False
    file_data = []

    time_out = 0.01  # should do the calculation for the timeout in efficient way
    max_buffer_size = 2 ** 16

    def __init__(self, nick_name=0) -> None:
        self.nick_name = nick_name
        self.client_sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.client_sock_udp = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        self.client_sock_udp.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)

    def three_way_size(self):
        try:
            self.client_sock_udp.settimeout(self.time_out)
            self.client_sock_udp.sendto('GIVE_SIZE'.encode('utf-8'), ('127.0.0.1', 55002))
            message, address = self.client_sock_udp.recvfrom(self.max_buffer_size)
            real_message = message.decode('utf-8')
            print(real_message)
            if real_message.split(':')[0] == 'SIZE':
                my_size = real_message.split(':')[1]
                self.client_sock_udp.sendto('ACK'.encode('utf-8'), ('127.0.0.1', 55002))
                self.client_sock_udp.settimeout(None)
                return my_size
            else:
                self.three_way_size()
        except:
            self.three_way_size()

    def three_way_handshake(self, counter):
        try:
            self.client_sock_udp.settimeout(self.time_out)
            self.client_sock_udp.sendto('SYN'.encode('utf-8'), ('127.0.0.1', 55002))
            message, address = self.client_sock_udp.recvfrom(self.max_buffer_size)
            if message.decode('utf-8') == 'ACK':
                self.client_sock_udp.sendto('ACK'.encode('utf-8'), ('127.0.0.1', 55002))
                self.client_sock_udp.settimeout(None)
                print("CONNECTED")
                return True
            else:
                print("CANNOT CONNECT TO THE SERVER")
                return False
        except:
            if counter <= 3:
                counter += 0
                self.three_way_handshake(counter)
            else:
                print("CANNOT CONNECT TO THE SERVER")
                return False

    def find_start_end(self, rcv_list):
        for i in range(0, len(rcv_list)):
            if rcv_list[i] == 0:
                start_index = i
                end_index = min(i + self.window_size, len(rcv_list))
                return start_index, end_index
        return 0, 0

    def three_way_finish(self):
        try:
            self.client_sock_udp.settimeout(self.time_out)
            self.client_sock_udp.sendto('FINISHED_FILE'.encode('utf-8'), ('127.0.0.1', 55002))
            message, address = self.client_sock_udp.recvfrom(self.max_buffer_size)
            if message.decode('utf-8') == 'ACK':
                self.client_sock_udp.sendto('ACK'.encode('utf-8'), ('127.0.0.1', 55002))
                self.client_sock_udp.settimeout(None)
                return True
            else:
                self.three_way_finish()
        except:
            self.three_way_finish()

    def udp_handler(self, port_num):
        bol = True
        done = False
        finished = True
        start_index = 0
        end_index = 0
        if not self.connected_udp:
            self.client_sock_udp.bind(('127.0.0.1', port_num))
            bol = self.three_way_handshake(0)
        # content = ""
        if bol:
            file_name = input("please enter a file name : ")
            # file_name = "big"
            file_name = file_name + ".txt"
            file = open(file_name, 'wb')
            self.connected_udp = True
            my_size = self.three_way_size()
            message, address = self.client_sock_udp.recvfrom(self.max_buffer_size)
            real_message = message.decode('utf-8')
            if message[1:len(message)].decode('utf-8') == 'EXIT':
                self.client_sock_udp.close()
            rcv_list = [0 for i in range(0, int(my_size))]
            buffer_list = [0 for i in range(0, int(my_size))]
            # if real_message.split(':')[0] == 'SIZE':
            #     got_size = True
            #     rcv_list = [0 for i in range(0, int(real_message.split(':')[1]))]
            #     buffer_list = [0 for i in range(0, int(real_message.split(':')[1]))]
            #     print("LISTS WERE CREATED!")
            #     while got_size:
            #         self.client_sock_udp.sendto('GOT_SIZE'.encode('utf-8'), address)
            #         packet_number_help_me =0
            #         data, _ = self.client_sock_udp.recvfrom(1024)
            #         if data.decode('utf-8') == 'ACK':
            #             got_size = False
            bool_confirm = True
            user_input = None
            while end_index <= len(rcv_list):
                for i in range(len(rcv_list) - self.window_size, len(rcv_list)):
                    # if start_index >= len(rcv_list) - self.window_size-1 and rcv_list[start_index + i] == 0:
                    # finished = False
                    if rcv_list[i] == 0:
                        finished = False
                if finished:
                    break
                start_index, end_index = self.find_start_end(rcv_list)
                if start_index == 0 and end_index == 0:
                    break
                for k in range(start_index, end_index):
                    if k == len(rcv_list):
                        break
                    data, _ = self.client_sock_udp.recvfrom(1024)
                    if data.decode('utf-8') == 'SIZE':
                        self.client_sock_udp.sendto('ACK', address)
                        continue
                    if data.decode('utf-8') == 'CONFIRM_PROCEED':
                        if user_input is None:
                            while user_input != 'yes' and user_input != 'no':
                                user_input = input("Do you want to proceed? [yes,no]")
                        if bool_confirm:
                            if user_input == 'yes':
                                self.client_sock_udp.sendto('PROCEED'.encode('utf-8'), address)
                                continue
                            elif user_input == 'no':
                                self.client_sock_udp.sendto('NO_PROCEED'.encode('utf-8'), address)
                                end_index = len(rcv_list) + 1
                                break
                        else:
                            if user_input == 'yes':
                                bool_confirm = True
                            elif user_input == 'no':
                                bool_confirm = True

                    seq_num = int.from_bytes(data[0:1], byteorder='big')
                    temp_start, temp_end = self.find_start_end(rcv_list)
                    temp = [i % 10 for i in range(temp_start, temp_end)]
                    if seq_num not in temp:
                        self.client_sock_udp.sendto(f'{seq_num}'.encode('utf-8'), address)
                    # if rcv_list[end_index-((end_index-seq_num)%self.window_size)]==1:
                    #     self.client_sock_udp.sendto(f'{seq_num}'.encode('utf-8'), (address))
                    #     print(seq_num)
                    # check if need to decode before putting in file
                    else:
                        if rcv_list[(end_index - (end_index - seq_num) % self.max_seq_num)] == 0:
                            buffer_list[(end_index - (end_index - seq_num) % self.max_seq_num)] = data[1:]
                            rcv_list[(end_index - (end_index - seq_num) % self.max_seq_num)] = 1
                            self.client_sock_udp.sendto(f'{seq_num}'.encode('utf-8'), address)
                            temp_start += 1
                            temp_end += 1
                            # print(temp_start, temp_end)
                # print(rcv_list[start_index:end_index])
            self.three_way_finish()
            if user_input == 'yes':
                for i in buffer_list:
                    ty = type(i)
                    if str(ty) == "<class 'bytes'>":
                        file.write(i)
                last_byte = buffer_list[len(rcv_list) - 1][-1]
                print(f'User {self.nick_name} downloaded 100% out of the file, Last byte is : {last_byte}')
                print("Done")
                j = 0
                for i in rcv_list:
                    j += 1
                    if i == 0:
                        print("At index :" + str(j))
            else:
                print("File transfer stopped by user.")

    def choose_nick_name(self):
        self.nick_name = input('choose a nick_name >>>')

    def client_receive(self):
        while True:
            if not self.connected:
                break
            try:
                message = self.client_sock.recv(1024).decode('utf-8')
                if str(message) == f'{self.nick_name}: Goodbye':
                    print("Goodbye")
                    self.client_sock.close()
                    self.client_sock_udp.close()
                elif message == "nick?":
                    self.client_sock.send(self.nick_name.encode('utf-8'))
                elif message == 'choose another nick':
                    self.nick_name = input('please choose another nick_name >>>')
                    self.client_sock.send(self.nick_name.encode('utf-8'))
                elif len(message) >= 14 and message[0:14] == "listen to port":
                    port_num = message[15:len(message)]
                    print(port_num)
                    receive_udp_thread = threading.Thread(target=self.udp_handler, args=(int(port_num),))
                    receive_udp_thread.start()
                else:
                    print(message)
            except:
                print('Error!')
                self.client_sock.close()
                exit(1)
                break

    def client_connect(self):
        self.client_sock.connect(('127.0.0.1', 55000))
        receive_thread = threading.Thread(target=self.client_receive)
        receive_thread.start()
        send_thread = threading.Thread(target=self.client_send)
        send_thread.start()

    def client_send(self):
        while self.connected:
            c_input = input("")
            message = f'{self.nick_name}: {c_input}'
            self.client_sock.send(message.encode('utf-8'))
            if c_input == "exit":
                self.connected = False


if __name__ == '__main__':
    client = Client2()
    client.choose_nick_name()
    client.client_connect()
