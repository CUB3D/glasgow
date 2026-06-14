from glasgow.applet.memory.mmc.base_msg import BaseMsg
from glasgow.applet.memory.mmc.cmd import build_cmd17
from glasgow.applet.memory.mmc.interface import MmcInterface
from glasgow.applet.memory.mmc.sd_command import SDCommand
from glasgow.applet.memory.mmc.state.base import BaseState


class SendCmd17(BaseState):
    async def on_message(self, m: BaseMsg, iface: MmcInterface):
        if m.cmd == SDCommand.CMD17.value:
            dat = await iface.read_data()

            # for x in range(len(dat) // 16):
            #     for i in range(8):
            #         print(dat[x*8+i], end=" ")
            #     print()

            self.block_addr += 1
            print(f"READ BLK {self.block_addr}")

            data_bytes = bytes(dat[:512])

            with open("./out.bin", "ab") as f:
                f.write(data_bytes)

            await iface.write_cmd_send_data_48(build_cmd17(self.block_addr))

    async def on_new_state(self, iface: MmcInterface):
        self.block_addr = 0
        await iface.write_cmd_send_data_48(build_cmd17(self.block_addr))