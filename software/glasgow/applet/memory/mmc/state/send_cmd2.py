from dataclasses import dataclass

from glasgow.applet.control.emmc.base_msg import BaseMsg
from glasgow.applet.control.emmc.cmd import build_cmd2
from glasgow.applet.control.emmc.interface import EmmcInterface
from glasgow.applet.control.emmc.registers.cid import CIDRegister
from glasgow.applet.control.emmc.sd_command import SDCommand
from glasgow.applet.control.emmc.state.base import BaseState

@dataclass
class R2MsgCid:
    cid: CIDRegister

    def __init__(self, v: int):
        res = (v >> 128) & 0b111111
        self.cid = CIDRegister((v & 0xFFFFFFFF_FFFFFFFF_FFFFFFFF_FFFFFFFF))

class SendCmd2(BaseState):
    async def on_message(self, m: BaseMsg, iface: EmmcInterface):
        if m.cmd == SDCommand.CMD2.value:
            #TODO: msg struct
            # This is a GET_ALL_CID response
            x = m.payload
            print(bin(x))
            cid = (x & 0xFFFFFFFF_FFFFFFFF_FFFFFFFF_FFFFFFFF)
            print("cid", hex(cid), bin(cid))

            c = R2MsgCid(x)
            print("mid", c.cid.mid)
            print("oem", c.cid.oem)
            print("prv", c.cid.prv)
            print("pnm", c.cid.pnm)
            print("psn", c.cid.psn)
            print("mdt", c.cid.mdt)
            print("crc", c.cid.crc)
            return True

    async def on_new_state(self, iface: EmmcInterface):
        await iface.write_cmd_send_bcr_136(build_cmd2())
