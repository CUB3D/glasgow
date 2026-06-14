from dataclasses import dataclass

from glasgow.applet.memory.mmc.base_msg import BaseMsg
from glasgow.applet.memory.mmc.cmd import build_cmd2
from glasgow.applet.memory.mmc.interface import MmcInterface
from glasgow.applet.memory.mmc.registers.cid import CIDRegister
from glasgow.applet.memory.mmc.sd_command import SDCommand
from glasgow.applet.memory.mmc.state.base import BaseState

@dataclass
class R2MsgCid:
    cid: CIDRegister

    def __init__(self, msg: BaseMsg):
        self.cid = CIDRegister((msg.payload & 0xFFFFFFFF_FFFFFFFF_FFFFFFFF_FFFFFFFF))

class SendCmd2(BaseState):
    async def on_message(self, m: BaseMsg, iface: MmcInterface):
        if m.cmd == SDCommand.CMD2.value:
            #TODO: crc check and how to fit with basemsg

            c = R2MsgCid(m)
            iface.card_cid = c.cid
            print("mid", c.cid.mid)
            print("oem", c.cid.oem)
            print("prv", c.cid.prv)
            print("pnm", c.cid.pnm)
            print("psn", c.cid.psn)
            print("mdt", c.cid.mdt)
            print("crc", c.cid.crc)
            return True

    async def on_new_state(self, iface: MmcInterface):
        await iface.write_cmd_send_bcr_136(build_cmd2())
