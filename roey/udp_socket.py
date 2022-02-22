import socket


class UDPSocket:

    def __init__(self, _server_ip: str, _sender_address: str, _receiver_address: str, _tcp_port: int):
        self.sender: str = _sender_address
        self.receiver: str = _receiver_address
        self.server: str = _server_ip
        self.port: int = _tcp_port + 15
        self.udp_soc = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.udp_soc.bind((self.server, self.port))
        self.file = None

    def send_file(self, _file):
        file = _file.encode()
        self.udp_soc.sendto(file, self.receiver)

    def file_from_sender(self):

    def file_to_receiver(self):
