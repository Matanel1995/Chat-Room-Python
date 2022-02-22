import socket


class UDPSocket:

    def __init__(self, _server_ip: str, _dest_ip: str, _tcp_port: int):
        self.dest_ip: str = _dest_ip
        self.server_ip: str = _server_ip
        self.port: int = _tcp_port + 15
        self.udp_soc = None
        self.file = None

    def open_socket(self):
        self.udp_soc = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.udp_soc.bind((self.server_ip, self.port))
        print('The UDP socket is online!')

    def close_socket(self):
        self.udp_soc.close()

    def send_file(self, _file):
        file = _file.encode()
        self.udp_soc.sendto(file, self.dest_ip)

    def file_from_sender(self):
        return None

    def file_to_receiver(self):
        return None
