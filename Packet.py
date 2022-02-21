
class Packet:
    seq: int
    acked: bool
    payload: bytearray
    len: int
    reTransmit: int

    def __init__(self, seq: int, payload: bytearray):
        self.seq =seq
        self.payload = payload
        self.len = len(payload)

    def setSeq(self, seq:int):
        self.seq = seq

    def setAck(self,ack: bool):
        self.acked = ack

    def setPayload(self,payload: bytearray):
        self.payload = payload

    def getPayLoad(self):
        return self.payload

    def getSeq(self):
        return self.seq

    def isAcked(self):
        return self.acked

    def __repr__(self):
        return "Seq number: " + self.seq