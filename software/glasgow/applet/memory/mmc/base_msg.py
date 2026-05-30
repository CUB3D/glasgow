from dataclasses import dataclass

from glasgow.applet.control.emmc.cmd import reverse_bits, crc7
from glasgow.applet.control.emmc.msg_dir import MsgDir


@dataclass
class BaseMsg:
    dir: MsgDir
    cmd: int
    payload: int
    crc: int

    def __init__(self, v: int):
        # assert v & 1 != 0
        self.crc = v & 0b1111111
        self.payload = (v >> 7) & 0xFFFF_FFFF
        self.cmd = (v >> 39) & 0b111111
        self.dir = MsgDir((v >> 45) & 1)

    def calc_crc(self):
        """
        Compute the CRC7 for this packet
        :return: The crc of this packet
        """
        msg_no_crc = 0b0 \
                     | (self.dir.value << 1) \
                     | (reverse_bits(self.cmd, 6) << 2) \
                     | (reverse_bits(self.payload, 32) << 8)

        return crc7(reverse_bits(msg_no_crc, 40).to_bytes(5, byteorder="big"))

    def crc_valid(self):
        """
        Check if the CRC7 of this packet matches the extracted value
        :return: True if the CRC7 from the packet, matches the computed CRC7 over the packets fields
        """
        return self.crc == self.calc_crc()