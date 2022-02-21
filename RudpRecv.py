import socket

ACK = 1
NAK = 0


class RudpRecv:
    startWindow: int # Pointer to window start index
    seq: int
    isBlocked: bool
    RUDPsocket: socket
    windows: list
    maxWindowSize: int
    recvPort: int
    sendPort: int



    def __init__(self,windowSize: int,recvPort: int, sendPort: int):
        self.maxWindowSize = windowSize
        self.recvPort = recvPort
        self.sendPort = sendPort




    def ackPacket(self, seqNum: int):
        if self.startWindow <= seqNum:
            if seqNum - self.startWindow < self.maxWindowSize:
                self.windows[seqNum - self.startWindow] = ACK

    def adjustwindow(self):
        while True:
            if self.windows[0] == ACK:
                for i in range(0, self.maxWindowSize-1):
                    self.windows[i] = self.windows[i+1]
                self.windows[self.maxWindowSize-1] = NAK
                self.startWindow = self.startWindow + 1
            else:
                break
