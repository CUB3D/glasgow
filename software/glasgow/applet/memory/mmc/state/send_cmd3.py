from dataclasses import dataclass

from glasgow.applet.memory.mmc.base_msg import BaseMsg
from glasgow.applet.memory.mmc.card_state import CardState
from glasgow.applet.memory.mmc.card_status import CardStatus
from glasgow.applet.memory.mmc.cmd import build_cmd3
from glasgow.applet.memory.mmc.interface import MmcInterface
from glasgow.applet.memory.mmc.mmc_error import MmcError
from glasgow.applet.memory.mmc.sd_command import SDCommand
from glasgow.applet.memory.mmc.state.base import BaseState

@dataclass
class Cmd3Resp:
    base: BaseMsg

    rca: int
    status: CardStatus

    def __init__(self, base: BaseMsg):
        self.base = base
        self.status = CardStatus(base.payload & 0xFFFF)
        self.rca = (base.payload >> 16) & 0xFFFF

class SendCmd3(BaseState):
    async def on_message(self, m: BaseMsg, iface: MmcInterface):
        if m.cmd == SDCommand.CMD3.value:
            msg = Cmd3Resp(m)
            if not msg.base.crc_valid():
                raise MmcError("CMD3 response has incorrect CRC value")
            if not msg.status.current_state == CardState.Ident:
                raise MmcError("CMD3 response indicated incorrect state")
            if msg.status.error:
                raise MmcError("CMD3 response indicated error")

            print("status", msg.status)
            print("rca", hex(msg.rca))
            iface.rca = msg.rca

            return True

    async def on_new_state(self, iface: MmcInterface):
        await iface.write_cmd_send_bcr_48(build_cmd3())