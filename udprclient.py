import sys
import threading
import socket


class UdprClient(threading.Thread):

    def __init__(self, nick_name, port_tuple):
        threading.Thread.__init__(self)
        self.fragment_size = 500  # in bytes
        self.window_size = 5
        self.max_seq_num = 10
        self.already_connect_udp = False
        self.file_data = []
        self.time_out = 0.01
        self.max_buffer_size = (2 ** 16) - 1
        self.nick_name = nick_name
        self.port_num = port_tuple[1]
        self.server_port = port_tuple[0]
        self.client_sock_udp = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        self.client_sock_udp.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)

    def three_way_handshake(self):
        """ Function to establish connection with the new client in reliable way
            work like TCP 3 way handshake"""
        self.client_sock_udp.settimeout(self.time_out)
        while True:
            try:
                self.client_sock_udp.sendto('SYN'.encode('utf-8'), ('127.0.0.1', self.server_port))
                message, adress = self.client_sock_udp.recvfrom(self.max_buffer_size)
                if message.decode('utf-8') == 'ACK':
                    self.client_sock_udp.sendto('ACK'.encode('utf-8'), ('127.0.0.1', self.server_port))
                    self.client_sock_udp.settimeout(None)
                    print("client_connect")
                    return True
            except:
                continue

    def find_start_end(self, rcv_list):
        """Function to find the first segment that we didn't receive yet to set the window size  """
        for i in range(0, len(rcv_list)):
            if rcv_list[i] == 0:
                start_index = i
                end_index = min(i + self.window_size, len(rcv_list))
                return start_index, end_index
        return 0, 0

    def close_connection(self):
        """ Function the responsible to close the connection in controlled way"""
        try:
            self.client_sock_udp.settimeout(self.time_out)
            self.client_sock_udp.sendto(f'FIN:{self.nick_name}'.encode('utf-8'), ('127.0.0.1', self.server_port))
            ans, _ = self.client_sock_udp.recvfrom(1024)
            if ans.decode('utf-8') == 'ACK':
                self.close_connection_2()
                return
            else:
                self.close_connection()
        except:
            self.close_connection()

    def close_connection_2(self):
        """ Part of the close connection"""
        try:
            self.client_sock_udp.settimeout(None)
            ans, _ = self.client_sock_udp.recvfrom(1024)
            while ans.decode('utf-8').split(":")[0] != 'FIN':
                ans, _ = self.client_sock_udp.recvfrom(1024)
            self.client_sock_udp.settimeout(self.time_out * 2)
            while True:
                self.client_sock_udp.sendto('ACK'.encode('utf-8'), ('127.0.0.1', self.server_port))
                ans, _ = self.client_sock_udp.recvfrom(1024)
        except:
            return

    def udp_handler(self):
        """Function to control the file transfer"""
        finished = True
        start_index = 0
        end_index = 0
        # Bind ourselves to the port number provided by the server
        self.client_sock_udp.bind(('127.0.0.1', self.port_num))
        # Try to connect, if connected three-way function will return true
        connected = self.three_way_handshake()
        if connected:
            real_message = ''
            message, address = self.client_sock_udp.recvfrom(self.max_buffer_size)
            try:
                real_message = message.decode('utf-8')
            except:
                pass
            # If we are still getting ACK from the three-way connection function (because of packet loss)
            # we send back ACK to the server until he gets it so he will know we are connected
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
            # If we are still getting messages that is not the packet size from the server (because of packet loss)
            # we send back SEND_SIZE to the server until he gets it so he will send us the size.
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
            # We got the size so we create our buffer to receive the file
            if real_message.split(':')[0] == 'SIZE':
                rcv_list = [0 for i in range(0, int(real_message.split(':')[1]))]
                buffer = [0 for i in range(0, int(real_message.split(':')[1]))]
            self.client_sock_udp.settimeout(None)
            bool_confirm = True
            user_input = None

            # Main loop
            while end_index <= len(rcv_list):
                # Check if we got the last 5 (window size) packet if so break and close connection
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

                    # If the server still sending us the SIZE that mean he didnt receive
                    # our ACK (because of packet loss)
                    # so we send him ACK again until he gets it
                    if decoded_data == 'SIZE':
                        self.client_sock_udp.sendto('ACK', address)
                        continue

                    # If the message is CONFIRM_PROCEED, the server stop the file transfer and wait for approve
                    # to continue
                    if decoded_data == 'CONFIRM_PROCEED':
                        if user_input is None:
                            # ask the user if he wants to continue if the answer is not yes or no we won't ask him again
                            # once he gives answer we change to bool parameter to true
                            while user_input != 'yes' and user_input != 'no':
                                user_input = input("You downloaded 40% of the file, Do you want to proceed? [yes,no]")
                            bool_confirm = True

                        # If the user give his answer we sent message to the server accordingly
                        # Proceed if yes , No proceed if no
                        if bool_confirm:
                            if user_input == 'yes':
                                self.client_sock_udp.sendto(f'PROCEED:{self.nick_name}'.encode('utf-8'), address)
                                continue
                            elif user_input == 'no':
                                self.client_sock_udp.sendto(f'NO_PROCEED:{self.nick_name}'.encode('utf-8'), address)
                                end_index = len(rcv_list) + 1
                                break

                    # Extract the seq number in order to send back ack
                    seq_num = int.from_bytes(data[0:1], byteorder='big')
                    temp_start, temp_end = self.find_start_end(rcv_list)
                    # Create a temp list with all the seq number we expect to receive now
                    temp = [i % 10 for i in range(temp_start, temp_end)]
                    # If it's not in the temp range we already got it, so we send ACK back
                    if seq_num not in temp:
                        self.client_sock_udp.sendto(f'{seq_num}'.encode('utf-8'), address)
                    # If it's in the temp range we save the packet data in our buffer
                    # And update our ack list, so we know we got it
                    # And send back ACK to the server
                    else:
                        if rcv_list[(end_index - (end_index - seq_num) % self.max_seq_num)] == 0:
                            buffer[(end_index - (end_index - seq_num) % self.max_seq_num)] = data[1:]
                            rcv_list[(end_index - (end_index - seq_num) % self.max_seq_num)] = 1
                            self.client_sock_udp.sendto(f'{seq_num}'.encode('utf-8'), address)
                            temp_start += 1
                            temp_end += 1

            # If we got here that mean we got all the file or the user didn't want to proceed
            self.close_connection()
            # If the user wanted to proceed, and we got here that mean we got all the file, so
            # we ask the user to enter a name which will be user to save the file
            if user_input == 'yes':
                last_byte = buffer[len(rcv_list) - 1][-1]
                print(f'User {self.nick_name} downloaded 100% out of the file, Last byte is : {last_byte}')
                file_name = input("please enter a file name + File extension : ")
                # Ask for a file name until it's not empty
                while file_name.strip(' ') == '':
                    file_name = input("please enter a file name + File extension: ")
                file = open(file_name, 'wb')
                for i in buffer:
                    ty = type(i)
                    if str(ty) == "<class 'bytes'>":
                        file.write(i)
                print("Done")

            # If the user didn't want to proceed we print "File transfer stopped by user." and close the thread
            else:
                print("File transfer stopped by user.")
                return

    def run(self) -> None:
        self.udp_handler()
        self.client_sock_udp.close()
        sys.exit()