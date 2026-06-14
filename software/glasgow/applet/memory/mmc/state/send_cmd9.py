from dataclasses import dataclass

from glasgow.applet.memory.mmc.base_msg import BaseMsg
from glasgow.applet.memory.mmc.cmd import build_cmd9
from glasgow.applet.memory.mmc.interface import MmcInterface
from glasgow.applet.memory.mmc.registers.csd import CSDRegister
from glasgow.applet.memory.mmc.sd_command import SDCommand
from glasgow.applet.memory.mmc.state.base import BaseState


@dataclass
class R2MsgCsd:
    csd: CSDRegister

    def __init__(self, msg: BaseMsg):
        self.csd = CSDRegister((msg.payload & 0xFFFFFFFF_FFFFFFFF_FFFFFFFF_FFFFFFFF))

class SendCmd9(BaseState):
    async def on_message(self, m: BaseMsg, iface: MmcInterface):
        #TODO:
        if m.cmd == SDCommand.CMD2.value:
            # #TODO: crc check and how to fit with basemsg

            c = R2MsgCsd(m)
            print(c)
            iface.card_csd = c.csd
            return True

    async def on_new_state(self, iface: MmcInterface):
        await iface.write_cmd_send_bcr_136(build_cmd9(iface.rca))
