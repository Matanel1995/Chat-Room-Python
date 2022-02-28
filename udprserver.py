import threading
import socket
import math
import os
import time


class UdprServer(threading.Thread):

    def __init__(self, port, nick_name, file_name, server_sock_udp, lock):
        threading.Thread.__init__(self)
        self.lock = lock
        self.max_packet_size = (2**16) - 1
        self.time_out = 0.01
        self.port = port
        self.file_name = file_name
        self.server_sock_udp = server_sock_udp
        self.fragment_size = 500
        self.seq_max = 10
        self.window_size = 5
        self.buffer = []
        self.ack_data = {}
        self.nick_name = nick_name

    def udp_transfer_files(self):
        connected = False
        file_size = os.path.getsize(self.file_name)
        segment_size = math.ceil(file_size/self.fragment_size)
        connected = self.three_way_handshake(False)
        if connected:
            self.update_buffer(segment_size)
            self.sliding_window()

    def three_way_handshake(self, syn):
        while True:
            try:
                self.server_sock_udp.settimeout(self.time_out)
                if not syn:
                    message, _ = self.server_sock_udp.recvfrom(self.max_packet_size)
                if message.decode('utf-8') == 'SYN' or syn:
                    syn = True
                    self.server_sock_udp.sendto('ACK'.encode('utf-8'), ('127.0.0.1', self.port))
                    ans, _ = self.server_sock_udp.recvfrom(self.max_packet_size)
                    if ans.decode('utf-8') == 'ACK':
                        self.server_sock_udp.settimeout(None)
                        return True
            except:
                continue

    """Function to read the requested file and split it by segment size """
    def update_buffer(self, segment_size):
        with open(self.file_name, 'rb') as f:
            j = 0
            while j <= segment_size:
                data = f.read(self.fragment_size)
                self.buffer.append(data)
                j += 1

    """Function to control the window for the Selective repeat algorithm"""
    def sliding_window(self):
        self.lock.acquire()
        start_index = 0
        end_index = 0
        finished = True
        nack = [0 for i in range(0, len(self.buffer))]
        bool_precent = True
        to_send = 'SIZE:' + str(len(nack) - 1)
        self.server_sock_udp.sendto(to_send.encode('utf-8'),
                                    ('127.0.0.1', self.port))
        while end_index <= len(nack):
            for i in range(len(nack)-self.window_size, len(nack)):
                if nack[i] == 0:
                    finished = False
            if finished:
                print("FINISHED")
                break
            start_index, end_index = self.find_start_end(nack)
            if start_index == 0 and end_index == 0:
                break
            for k in range(start_index, end_index):
                if nack[k] == 0:
                    data = self.buffer[k]
                    ind = (k % self.seq_max).to_bytes(1, byteorder='big')
                    packet = ind+data
                    self.server_sock_udp.sendto(packet, ('127.0.0.1', self.port))
            precent = (start_index / len(nack)) * 100
            self.server_sock_udp.settimeout(self.time_out)
            precent = "{:.2f}".format(precent)
            if self.check_ack(nack, start_index, end_index, precent) == 0:
                print("File transferred")
                break
            if bool_precent and float(precent) > 40:
                bool_precent = False
                self.lock.release()
                while True:
                    try:
                        self.server_sock_udp.sendto('CONFIRM_PROCEED'.encode('utf-8'),
                                                    ('127.0.0.1', self.port))
                        msg, _ = self.server_sock_udp.recvfrom(1024)
                        real_msg = msg.decode('utf-8').split(":")
                        if real_msg[0] == 'PROCEED' and real_msg[1] == self.nick_name:
                            self.lock.acquire()
                            break
                        elif real_msg[0] == 'NO_PROCEED' and real_msg[1] == self.nick_name:
                            print("GOT NO PROCEED!!!!!!!!!!!!!!!!!!!!!!!!!!!!")
                            self.lock.acquire()
                            msg, _ = self.server_sock_udp.recvfrom(1024)
                            print(msg.decode('utf-8'))
                            while msg.decode('utf-8') != 'FIN':
                                msg, _ = self.server_sock_udp.recvfrom(1024)
                                #if self.check_ack(nack, start_index, end_index, precent) == 0:
                                    #end_index = len(nack) + 1
                                    #break
                            end_index = len(nack) + 1
                            self.close_connection()
                            self.lock.release()
                            break
                        else:
                            continue
                    except:
                        pass

    """Function to fine the first segment that we didn't received yet to set the window size  """
    def find_start_end(self, nack):
        for i in range(0, len(nack)):
            if nack[i] == 0:
                start_index = i
                end_index = min(i + self.window_size, len(nack)-1)
                return start_index, end_index

    """Function to recive client response and act accordingly 
        - If its ACK for segment that in the range of start and end index, it will update the nack list 
          in orded to not send this segment again
        - If its a FIN massage that mean the client recived all the file and want to close connection
        - If its size , the client want to know the size of the file , it will send the size to the client
    """
    def check_ack(self, nack, start_index, end_index, precent):
        while True:
            try:
                ack, _ = self.server_sock_udp.recvfrom(1024)
                if ack.decode('utf-8') == 'FIN':
                    self.close_connection()
                    return 0
                to_send = 'SIZE:' + str((len(nack)-1))
                if ack.decode('utf-8') == 'SEND_SIZE':
                    self.server_sock_udp.sendto(to_send.encode('utf-8'),
                                                ('127.0.0.1', self.port))
                for i in range(start_index, end_index):
                    if i % 10 == int(ack.decode('utf-8')) % 10:
                        nack[i] = 1
                        if float(precent) > 0:
                            print(f'Send {precent}% from the file! To: {self.nick_name}')

            except :
                return 1

    def close_connection(self):
        try:
            print("IN CLOSE CONNECTION")
            self.server_sock_udp.settimeout(None)
            ans, _ = self.server_sock_udp.recvfrom(1024)
            print(ans.decode('utf-8'))
            self.server_sock_udp.settimeout(self.time_out)
            while ans.decode('utf-8') != 'FIN':
                ans, _ = self.server_sock_udp.recvfrom(self.max_packet_size)
            while ans.decode('utf-8') == 'FIN':
                self.server_sock_udp.sendto('ACK'.encode('utf-8'), ('127.0.0.1', self.port))
                ans, _ = self.server_sock_udp.recvfrom(self.max_packet_size)
        except:
            self.close_connection_2()
            return

    def close_connection_2(self):
        try:
            print("IN CLOSE CONNECTION2")
            self.server_sock_udp.settimeout(self.time_out)
            self.server_sock_udp.sendto('FIN'.encode('utf-8'), ('127.0.0.1', self.port))
            ans, _ = self.server_sock_udp.recvfrom(self.max_packet_size)
            if ans.decode('utf-8') == 'ACK':
                return
        except:
            self.close_connection_2()

    def is_alive(self) -> bool:
        return threading.Thread.is_alive(self)

    def run(self) -> None:
        self.udp_transfer_files()
        print("AFTER FILE TRANSFERD")

