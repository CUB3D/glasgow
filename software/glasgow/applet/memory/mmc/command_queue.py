from typing import List

from glasgow.applet.memory.mmc.base_msg import BaseMsg
from glasgow.applet.memory.mmc.interface import MmcInterface
from glasgow.applet.memory.mmc.state.base import BaseState


class SDCommandQueue:
    queue: List[BaseState]

    def __init__(self):
        self.queue = []

    def add(self, x: BaseState):
        self.queue.append(x)

    async def handle_msg(self, m: BaseMsg, iface: MmcInterface):
        res = await self.queue[0].on_message(m, iface)
        if res:
            self.queue.pop(0)
            if len(self.queue) > 0:
                await self.queue[0].on_new_state(iface)

    async def process_incoming_messages(self, iface: MmcInterface):
        # Keep processing while we have commands to handle
        while len(self.queue) > 0:

            typ = await iface.read_1()
            print("ty", hex(typ))
            if typ == 0xa1:
                x = await iface.read_5()

                m = BaseMsg(x)

                print("cmd", m.cmd, bin(m.cmd))
                # print("payload", hex(m.payload), bin(m.payload))
                # print("crc", hex(m.crc), bin(m.crc))
                # print("Valid", "TRUE" if m.crc_valid() else "!FALSE!")
                # print(", ".join([x for x in ("00000000" + bin(x)[2:])[-48:]]))

                await self.handle_msg(m, iface)

            # CMD2 resp
            if typ == 0xa3:
                x = await iface.read_17()
                y = BaseMsg(0)
                y.cmd = 2
                y.payload = x

                await self.handle_msg(y, iface)

            print("-----------")