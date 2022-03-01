import threading
import socket
import math
import os


class UdprServer(threading.Thread):

    def __init__(self, port_tuple, nick_name, file_name):
        threading.Thread.__init__(self)
        self.max_packet_size = (2**16) - 1
        self.time_out = 0.01
        self.port = port_tuple[1]
        self.file_name = file_name
        self.server_sock_udp = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        self.server_sock_udp.bind(('127.0.0.1', port_tuple[0]))
        self.fragment_size = 500
        self.seq_max = 10
        self.window_size = 5
        self.buffer = []
        self.ack_data = {}
        self.nick_name = nick_name
        print(f'Server port num {port_tuple[0]} client port num {self.port}')

    def udp_transfer_files(self):
        """ Function to start the process of sending the file in a reliable way to the client"""
        connected = False
        file_size = os.path.getsize(self.file_name)
        segment_size = math.ceil(file_size/self.fragment_size)
        connected = self.three_way_handshake(False)
        if connected:
            self.update_buffer(segment_size)
            self.sliding_window()
            print("in udp transfer file")

    def three_way_handshake(self, syn):
        """ Function to establish connection with the new client in reliable way
            work like TCP 3 way handshake"""
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

    def update_buffer(self, segment_size):
        """Function to read the requested file and split it by segment size """
        with open(self.file_name, 'rb') as f:
            j = 0
            while j <= segment_size:
                data = f.read(self.fragment_size)
                self.buffer.append(data)
                j += 1

    def sliding_window(self):
        """Function to control the window for the Selective repeat algorithm"""
        start_index = 0
        end_index = 0
        finished = True
        nack = [0 for i in range(0, len(self.buffer))]  # Create list of 0 to keep track of received packets
        bool_precent = True  # Boolean parameter to check we dont stop twice to ask of proceed
        # Send to the client the size of the file in packets so he can be prepared
        to_send = 'SIZE:' + str(len(nack) - 1)
        self.server_sock_udp.sendto(to_send.encode('utf-8'),
                                    ('127.0.0.1', self.port))
        # Main Loop
        while end_index <= len(nack):
            # Check if we got the last 5 (window size) packet acks if so break and close connection
            for i in range(len(nack)-self.window_size, len(nack)):
                if nack[i] == 0:
                    finished = False
            if finished:
                break
            start_index, end_index = self.find_start_end(nack)  # Find the first packet that wasn't received
            if start_index == 0 and end_index == 0:
                break
            for k in range(start_index, end_index):
                if nack[k] == 0:
                    data = self.buffer[k]
                    ind = (k % self.seq_max).to_bytes(1, byteorder='big')  # Find the sequence number
                    packet = ind+data # add the sequence number before the data and sending it to the client
                    self.server_sock_udp.sendto(packet, ('127.0.0.1', self.port))
            precent = (start_index / len(nack)) * 100  # Calculate how much of the file already transfer
            self.server_sock_udp.settimeout(self.time_out)
            precent = "{:.2f}".format(precent)  # Changing the number to a format with 2 digits after decimal

            # If we got 0 from check_ack function that mean we closed the connection, and we can exit the thread
            if self.check_ack(nack, start_index, end_index, precent) == 0:
                end_index = len(nack) + 1
                print("File transferred")
                return

            # Check if its time to ask the client if he wants to proceed
            if bool_precent and float(precent) > 40:
                # Change the boolean parameter to false, so we won't stop here again
                bool_precent = False
                while True:
                    try:
                        self.server_sock_udp.sendto('CONFIRM_PROCEED'.encode('utf-8'),
                                                    ('127.0.0.1', self.port))
                        msg, _ = self.server_sock_udp.recvfrom(1024)
                        real_msg = msg.decode('utf-8').split(":")

                        # Got proceed answer
                        if real_msg[0] == 'PROCEED' and real_msg[1] == self.nick_name:
                            break

                        # Got no proceed answer
                        elif real_msg[0] == 'NO_PROCEED' and real_msg[1] == self.nick_name:
                            msg, _ = self.server_sock_udp.recvfrom(1024)
                            print(msg.decode('utf-8'))
                            while msg.decode('utf-8').split(":")[0] != 'FIN' and msg.decode('utf-8').split(":")[1] ==\
                                    self.nick_name:
                                msg, _ = self.server_sock_udp.recvfrom(1024)
                            end_index = len(nack) + 1
                            break
                        else:
                            continue
                    except:
                        pass
        # Call to close connection function
        self.close_connection()

    def find_start_end(self, nack):
        """Function to find the first segment that we didn't receive an ack for yet to set the window size  """
        for i in range(0, len(nack)):
            if nack[i] == 0:
                start_index = i
                end_index = min(i + self.window_size, len(nack)-1)
                return start_index, end_index

    def check_ack(self, nack, start_index, end_index, precent):
        """Function to recive client response and act accordingly
            - If its ACK for segment that in the range of start and end index, it will update the nack list
              in orded to not send this segment again
            - If its a FIN massage that mean the client recived all the file and want to close connection
            - If its size , the client want to know the size of the file , it will send the size to the client
        """
        while True:
            try:
                ack, _ = self.server_sock_udp.recvfrom(1024)
                # If its FIN message that mean the client want to close connection so we call
                # close connection function and return 0
                if ack.decode('utf-8').split(":")[0] == 'FIN' and ack.decode('utf-8').split(":")[1] == self.nick_name:
                    self.close_connection()
                    return 0
                to_send = 'SIZE:' + str((len(nack)-1))

                # If the client ask for the size of all packets
                if ack.decode('utf-8') == 'SEND_SIZE':
                    self.server_sock_udp.sendto(to_send.encode('utf-8'),
                                                ('127.0.0.1', self.port))

                # If none of the above we check the ask message the client send us and mark it to ourselves
                for i in range(start_index, end_index):
                    if i % 10 == int(ack.decode('utf-8')) % 10:
                        nack[i] = 1
                        if float(precent) > 0:
                            print(f'Send {precent}% from the file! To: {self.nick_name}')
            except :
                return 1

    def close_connection(self):
        """ Function the responsible to close the connection in controlled way"""
        try:
            self.server_sock_udp.settimeout(None)
            ans, _ = self.server_sock_udp.recvfrom(1024)
            self.server_sock_udp.settimeout(self.time_out)
            while ans.decode('utf-8').split(":")[0] != 'FIN':
                ans, _ = self.server_sock_udp.recvfrom(self.max_packet_size)
            while ans.decode('utf-8').split(":")[0] == 'FIN' and ans.decode('utf-8').split(":")[1] == self.nick_name:
                self.server_sock_udp.sendto('ACK'.encode('utf-8'), ('127.0.0.1', self.port))
                ans, _ = self.server_sock_udp.recvfrom(self.max_packet_size)
        except:
            self.close_connection_2()
            return

    def close_connection_2(self):
        """ Part of the close connection"""
        try:
            self.server_sock_udp.settimeout(self.time_out)
            self.server_sock_udp.sendto(f'FIN:{self.nick_name}'.encode('utf-8'), ('127.0.0.1', self.port))
            ans, _ = self.server_sock_udp.recvfrom(self.max_packet_size)
            if ans.decode('utf-8') == 'ACK':
                return
        except:
            self.close_connection_2()

    # def is_alive(self) -> bool:
    #     return threading.Thread.is_alive(self)

    def run(self) -> None:
        self.udp_transfer_files()
        self.server_sock_udp.close()