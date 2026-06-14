from dataclasses import dataclass

from glasgow.applet.memory.mmc.mmc_error import MmcError
from glasgow.applet.memory.mmc.base_msg import BaseMsg
from glasgow.applet.memory.mmc.interface import MmcInterface
from glasgow.applet.memory.mmc.sd_command import SDCommand
from glasgow.applet.memory.mmc.state.base import BaseState

@dataclass
class Cmd8Resp:
    base: BaseMsg

    check: int
    voltage: int

    def __init__(self, base: BaseMsg):
        self.base = base
        self.check = base.payload & 0xFF
        self.voltage = (base.payload >> 8) & 0xFF


class SendCmd8(BaseState):
    async def on_message(self, m: BaseMsg, iface: MmcInterface):
        if m.cmd == SDCommand.CMD8.value:
            msg = Cmd8Resp(m)
            if not msg.base.crc_valid():
                raise MmcError("CMD8 response has incorrect CRC value")
            if msg.check != 0xAA:
                raise MmcError("CMD8 response has incorrect check value")
            if msg.voltage != 0b0001:
                raise MmcError("CMD8 response has different voltage to what we requested")
            return True

    async def on_new_state(self, iface: MmcInterface):
        pass