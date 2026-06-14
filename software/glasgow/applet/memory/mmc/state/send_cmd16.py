from glasgow.applet.memory.mmc.base_msg import BaseMsg
from glasgow.applet.memory.mmc.card_state import CardState
from glasgow.applet.memory.mmc.card_status import CardStatus
from glasgow.applet.memory.mmc.cmd import build_cmd16
from glasgow.applet.memory.mmc.interface import MmcInterface
from glasgow.applet.memory.mmc.mmc_error import MmcError
from glasgow.applet.memory.mmc.r1_response import R1Response
from glasgow.applet.memory.mmc.sd_command import SDCommand
from glasgow.applet.memory.mmc.state.base import BaseState


class SendCmd16(BaseState):
    async def on_message(self, m: BaseMsg, iface: MmcInterface):
        if m.cmd == SDCommand.CMD16.value:
            msg = R1Response(m)
            print(msg)
            if not msg.base.crc_valid():
                raise MmcError("CMD16 response has incorrect CRC value")
            if not msg.status.current_state == CardState.Tran:
                raise MmcError("CMD16 response indicated incorrect state")
            if msg.status.error:
                raise MmcError("CMD16 response indicated error")
            return True

    async def on_new_state(self, iface: MmcInterface):
        await iface.write_cmd_send_bcr_48(build_cmd16())
