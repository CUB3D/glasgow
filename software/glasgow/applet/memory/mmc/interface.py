from logging import Logger
from typing import Optional

from glasgow.applet.memory.mmc.registers.cid import CIDRegister
from glasgow.applet.memory.mmc.registers.csd import CSDRegister
from glasgow.applet.memory.mmc.registers.ocr import OCRVoltageWindow
from glasgow.applet.memory.mmc.registers.scr import SCRRegister

IN_CMD_SEND_BCR48 = 0x01
IN_CMD_SEND_BCR136 = 0x02
IN_CMD_SEND_DATA48 = 0x03
IN_CMD_FILL_BUFFER = 0x04
IN_CMD_READ_BUFFER = 0x05
IN_CMD_RESET = 0x06

class MmcInterface:
    logger: Logger

    card_cid: CIDRegister
    rca: int
    card_scr: SCRRegister
    card_csd: CSDRegister
    ocr: OCRVoltageWindow
    ccs: bool
    uhsii: bool
    s18a: bool

    def __init__(self, interface, logger: Logger):
        self.lower  = interface
        self.logger = logger

    async def read_5(self):
        x = int.from_bytes(await self.lower.read(48 // 8), byteorder="big")
        return x
    async def read_1(self):
        x = int.from_bytes(await self.lower.read(8 // 8), byteorder="big")
        return x
    async def read_17(self):
        x = int.from_bytes(await self.lower.read(136 // 8), byteorder="big")
        # for _ in range(17):
        #     x = await self.read_1()
        #     print(x)
        return x

    async def write_1(self, v):
        await self.lower.write(int.to_bytes(v, 1, byteorder="big"))

    async def write_cmd_send_bcr_48(self, cmd: int):
        print("Sending BCR 48 cmd")
        await self.lower.write(int.to_bytes(IN_CMD_SEND_BCR48, 1, byteorder="big"))
        await self.lower.write(int.to_bytes(cmd, 48//8, byteorder="big"))

    async def write_cmd_send_data_48(self, cmd: int):
        print("Sending DATA 48 cmd")
        await self.lower.write(int.to_bytes(IN_CMD_SEND_DATA48, 1, byteorder="big"))
        await self.lower.write(int.to_bytes(cmd, 48//8, byteorder="big"))

    async def write_cmd_send_bcr_136(self, cmd: int):
        print("Sending BCR 136 cmd")
        await self.lower.write(int.to_bytes(IN_CMD_SEND_BCR136, 1, byteorder="big"))
        await self.lower.write(int.to_bytes(cmd, 48//8, byteorder="big"))

    async def read_data(self):
        print("Sending data read")
        # await self.lower.write(int.to_bytes(IN_CMD_READ_BUFFER, 1, byteorder="big"))
        # await self.lower.write(int.to_bytes(0, 48//8, byteorder="big")) # TODO: remove

        buf = []

        for x in range((512+16)):
            data = await self.lower.read(1)
            buf.append(data[0])

            print(hex(data[0]), end=" ")
            if x % 8 == 7:
                print()
        print("###")


        return buf

        # data = await self.lower.read(512+16)
        # return data

    async def reset(self):
        print("Sending reset")
        await self.lower.write(int.to_bytes(IN_CMD_RESET, 1, byteorder="big"))