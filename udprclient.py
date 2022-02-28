import sys
import threading
import socket

class UdprClient(threading.Thread):

    def __init__(self, nick_name, porn_num):
        threading.Thread.__init__(self)
        self.fragment_size = 500  # in bytes
        self.window_size = 5
        self.max_seq_num = 10
        self.already_connect_udp = False
        self.file_data = []
        self.time_out = 0.01  # should do the calculation for the timeout in efficient way
        self.max_buffer_size = (2 ** 16) - 1
        self.nick_name = nick_name
        self.port_num = int(porn_num)
        self.client_sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.client_sock_udp = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        self.client_sock_udp.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)

    def three_way_handshake(self):
        self.client_sock_udp.settimeout(self.time_out)
        while True:
            try:
                self.client_sock_udp.sendto('SYN'.encode('utf-8'), ('127.0.0.1', 55001))
                message, adress = self.client_sock_udp.recvfrom(self.max_buffer_size)
                if message.decode('utf-8') == 'ACK':
                    self.client_sock_udp.sendto('ACK'.encode('utf-8'), ('127.0.0.1', 55001))
                    self.client_sock_udp.settimeout(None)
                    print("client_connect")
                    return True
            except:
                continue

    def find_start_end(self, rcv_list):
        for i in range(0, len(rcv_list)):
            if rcv_list[i] == 0:
                start_index = i
                end_index = min(i + self.window_size, len(rcv_list))
                return start_index, end_index
        return 0, 0


    def close_connection(self):
        try:
            self.client_sock_udp.settimeout(self.time_out)
            self.client_sock_udp.sendto('FIN'.encode('utf-8'), ('127.0.0.1', 55001))
            ans, _ = self.client_sock_udp.recvfrom(1024)
            if ans.decode('utf-8') == 'ACK':
                print("GO TO CLOSE CONNECTION 2")
                self.close_connection_2()
                return
            else:
                self.close_connection()
        except:
            self.close_connection()

    def close_connection_2(self):
        print("IN CLOSE CONNECTION 2")
        try:
            self.client_sock_udp.settimeout(None)
            ans, _ = self.client_sock_udp.recvfrom(1024)
            while ans.decode('utf-8') != 'FIN':
                ans, _ = self.client_sock_udp.recvfrom(1024)
            self.client_sock_udp.settimeout(self.time_out * 2)
            while True:
                self.client_sock_udp.sendto('ACK'.encode('utf-8'), ('127.0.0.1', 55001))
                ans, _ = self.client_sock_udp.recvfrom(1024)
        except:
            return

    def udp_handler(self):
        finished = True
        start_index = 0
        end_index = 0
        self.client_sock_udp.bind(('127.0.0.1', self.port_num))
        connected = self.three_way_handshake()
        if connected:
            real_message = ''
            message, address = self.client_sock_udp.recvfrom(self.max_buffer_size)
            try:
                real_message = message.decode('utf-8')
            except:
                pass
            while real_message == 'ACK':
                try:
                    self.client_sock_udp.settimeout(self.time_out)
                    self.client_sock_udp.sendto('ACK'.encode('UTF-8'), address)
                    message, address = self.client_sock_udp.recvfrom(self.max_buffer_size)
                    real_message = message.decode('utf-8')
                except:
                    continue
            try:
                real_message = message.decode('utf-8')
            except:
                pass
            while real_message.split(':')[0] != 'SIZE':
                try:
                    self.client_sock_udp.settimeout(self.time_out)
                    self.client_sock_udp.sendto('SEND_SIZE'.encode('utf-8'), address)
                    message, address = self.client_sock_udp.recvfrom(self.max_buffer_size)
                    real_message = message.decode('utf-8')
                except:
                    continue
            try:
                real_message = message.decode('utf-8')
            except:
                pass
            if real_message.split(':')[0] == 'SIZE':
                rcv_list = [0 for i in range(0, int(real_message.split(':')[1]))]
                buffer = [0 for i in range(0, int(real_message.split(':')[1]))]
            self.client_sock_udp.settimeout(None)
            bool_confirm = True
            user_input = None
            while end_index <= len(rcv_list):
                for i in range(len(rcv_list) - self.window_size, len(rcv_list)):
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
                    decoded_data = ''
                    try:
                        decoded_data = data.decode('utf-8')
                    except:
                        pass
                    if decoded_data == 'SIZE':
                        self.client_sock_udp.sendto('ACK', (address))
                        continue
                    if decoded_data == 'CONFIRM_PROCEED':
                        if user_input is None:
                            while user_input != 'yes' and user_input != 'no':
                                user_input = input("You downloaded 40% of the file, Do you want to proceed? [yes,no]")
                            bool_confirm = True
                        if bool_confirm:
                            if user_input == 'yes':
                                self.client_sock_udp.sendto(f'PROCEED:{self.nick_name}'.encode('utf-8'), (address))
                                continue
                            elif user_input == 'no':
                                self.client_sock_udp.sendto(f'NO_PROCEED:{self.nick_name}'.encode('utf-8'), (address))
                                end_index = len(rcv_list) + 1
                                break
                        # else:
                        #     if user_input == 'yes':
                        #         bool_confirm = True
                        #     elif user_input == 'no':
                        #         bool_confirm = True
                    seq_num = int.from_bytes(data[0:1], byteorder='big')
                    temp_start, temp_end = self.find_start_end(rcv_list)
                    temp = [i % 10 for i in range(temp_start, temp_end)]
                    if seq_num not in temp:
                        self.client_sock_udp.sendto(f'{seq_num}'.encode('utf-8'), (address))
                    else:
                        if rcv_list[(end_index - (end_index - seq_num) % self.max_seq_num)] == 0:
                            buffer[(end_index - (end_index - seq_num) % self.max_seq_num)] = data[1:]
                            rcv_list[(end_index - (end_index - seq_num) % self.max_seq_num)] = 1
                            self.client_sock_udp.sendto(f'{seq_num}'.encode('utf-8'), (address))
                            temp_start += 1
                            temp_end += 1
            print("SEND NO PROCEED TO SERVER")
            self.close_connection()
            print("DO I GET HERE?")
            if user_input == 'yes':
                last_byte = buffer[len(rcv_list) - 1][-1]
                print(f'User {self.nick_name} downloaded 100% out of the file, Last byte is : {last_byte}')
                file_name = input("please enter a file name : ")
                while file_name.strip(' ') == '':
                    file_name = input("please enter a file name : ")
                file = open(file_name, 'wb')
                for i in buffer:
                    ty = type(i)
                    if str(ty) == "<class 'bytes'>":
                        file.write(i)
                print("Done")
            else:
                print("File transfer stopped by user.")
                return

    def run(self) -> None:
        self.udp_handler()
        self.client_sock_udp.close()
        sys.exit()
