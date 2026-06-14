from glasgow.applet.memory.mmc.base_msg import BaseMsg
from glasgow.applet.memory.mmc.card_status import CardStatus
from glasgow.applet.memory.mmc.cmd import build_acmd51, build_cmd55
from glasgow.applet.memory.mmc.interface import MmcInterface
from glasgow.applet.memory.mmc.registers.scr import CSRRegister
from glasgow.applet.memory.mmc.sd_command import SDCommand
from glasgow.applet.memory.mmc.state.base import BaseState


class SendACmd51(BaseState):
    async def on_message(self, m: BaseMsg, iface: MmcInterface):
        # If this is a response to the CMD55
        if m.cmd == SDCommand.CMD55.value:
            status = CardStatus(m.payload)
            print(status)
            # Send ACMD51
            await iface.write_cmd_send_data_48(build_acmd51())
        # If this is the response to the ACMD
        elif m.cmd == SDCommand.CMD51.value:
            status = CardStatus(m.payload)
            print(status)

            dat = await iface.read_data()

            for x in range(len(dat) // 16):
                for i in range(8):
                    print(dat[x * 8 + i], end=" ")
                print()

            # Only top bit of last byte (end bit) so skip
            scr = int.from_bytes(dat[:10], "big")

            #TODO: is this csr?? or scr??
            s = CSRRegister(scr)
            print(s)
            return True

    async def on_new_state(self, iface: MmcInterface):
        # Because this is an ACMD, we have to send cmd55 first
        await iface.write_cmd_send_bcr_48(build_cmd55(rca=iface.rca))
