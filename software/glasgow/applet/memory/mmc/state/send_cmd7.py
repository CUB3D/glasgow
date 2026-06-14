from glasgow.applet.memory.mmc.base_msg import BaseMsg
from glasgow.applet.memory.mmc.card_status import CardStatus
from glasgow.applet.memory.mmc.cmd import build_cmd7
from glasgow.applet.memory.mmc.interface import MmcInterface
from glasgow.applet.memory.mmc.sd_command import SDCommand
from glasgow.applet.memory.mmc.state.base import BaseState


class SendCmd7(BaseState):
    async def on_message(self, m: BaseMsg, iface: MmcInterface):
        if m.cmd == SDCommand.CMD7.value:
            status = CardStatus(m.payload)
            print(status)
            return True

    async def on_new_state(self, iface: MmcInterface):
        await iface.write_cmd_send_bcr_48(build_cmd7(iface.rca))