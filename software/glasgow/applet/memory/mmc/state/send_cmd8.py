from glasgow.applet.control.emmc.base_msg import BaseMsg
from glasgow.applet.control.emmc.interface import EmmcInterface
from glasgow.applet.control.emmc.sd_command import SDCommand
from glasgow.applet.control.emmc.state.base import BaseState


class SendCmd8(BaseState):
    async def on_message(self, m: BaseMsg, iface: EmmcInterface):
        if m.cmd == SDCommand.CMD8.value:
            # TODO: parse
            return True
        # else:
        #     await iface.reset()
        #     return None

    async def on_new_state(self, iface: EmmcInterface):
        pass