from dataclasses import dataclass

from glasgow.applet.control.emmc.base_msg import BaseMsg
from glasgow.applet.control.emmc.card_status import CardStatus
from glasgow.applet.control.emmc.cmd import build_acmd41, build_cmd55
from glasgow.applet.control.emmc.interface import EmmcInterface
from glasgow.applet.control.emmc.registers.ocr import OCRVoltageWindow
from glasgow.applet.control.emmc.sd_command import SDCommand
from glasgow.applet.control.emmc.state.base import BaseState

@dataclass
class Acmd41Response:
    busy: bool
    ccs: bool
    uhsii: bool
    s18a: bool
    ocr: OCRVoltageWindow

    def __init__(self, v: int):
        self.busy = (v >> 31) & 1 != 0
        self.ccs = (v >> 30) & 1 != 0
        self.uhsii = (v >> 29) & 1 != 0
        self.s18a = (v >> 24) & 1 != 0
        self.ocr = OCRVoltageWindow(((v >> 8) & 0xFFFF) << 8)

class SendACmd41(BaseState):
    async def on_message(self, m: BaseMsg, iface: EmmcInterface):
        # If this is a response to the CMD55
        if m.cmd == SDCommand.CMD55.value:
            status = CardStatus(m.payload)
            print(status)
            # Send ACMD41
            await iface.write_cmd_send_bcr_48(build_acmd41())
        # If this is the response to the ACMD
        elif m.cmd == 63:
            resp = Acmd41Response(m.payload)
            print(resp)

            # If not busy, card isn't ready, we need to rety
            if resp.busy:
                # Go to next state, card is ready
                return True
            else:
                # Retry
                await iface.write_cmd_send_bcr_48(build_cmd55(rca=0))

    async def on_new_state(self, iface: EmmcInterface):
        # Because this is an ACMD, we have to send cmd55 first
        await iface.write_cmd_send_bcr_48(build_cmd55(rca=0))