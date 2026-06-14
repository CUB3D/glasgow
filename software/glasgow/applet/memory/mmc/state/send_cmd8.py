from glasgow.applet.memory.mmc.base_msg import BaseMsg
from glasgow.applet.memory.mmc.interface import MmcInterface
from glasgow.applet.memory.mmc.sd_command import SDCommand
from glasgow.applet.memory.mmc.state.base import BaseState


class SendCmd8(BaseState):
    async def on_message(self, m: BaseMsg, iface: MmcInterface):
        if m.cmd == SDCommand.CMD8.value:
            # TODO: parse
            return True
        # else:
        #     await iface.reset()
        #     return None

    async def on_new_state(self, iface: MmcInterface):
        pass