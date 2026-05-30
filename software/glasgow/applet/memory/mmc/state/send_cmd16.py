from glasgow.applet.control.emmc.base_msg import BaseMsg
from glasgow.applet.control.emmc.card_status import CardStatus
from glasgow.applet.control.emmc.cmd import build_cmd16
from glasgow.applet.control.emmc.interface import EmmcInterface
from glasgow.applet.control.emmc.sd_command import SDCommand
from glasgow.applet.control.emmc.state.base import BaseState


class SendCmd16(BaseState):
    async def on_message(self, m: BaseMsg, iface: EmmcInterface):
        if m.cmd == SDCommand.CMD16.value:
            status = CardStatus(m.payload)
            print(status)

            self.foo = 0
            return True

    async def on_new_state(self, iface: EmmcInterface):
        await iface.write_cmd_send_bcr_48(build_cmd16())
