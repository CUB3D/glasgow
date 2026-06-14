from dataclasses import dataclass

from glasgow.applet.memory.mmc.base_msg import BaseMsg
from glasgow.applet.memory.mmc.cmd import build_acmd41, build_cmd55
from glasgow.applet.memory.mmc.r1_response import R1Response
from glasgow.applet.memory.mmc.interface import MmcInterface
from glasgow.applet.memory.mmc.mmc_error import MmcError
from glasgow.applet.memory.mmc.registers.ocr import OCRVoltageWindow
from glasgow.applet.memory.mmc.sd_command import SDCommand
from glasgow.applet.memory.mmc.state.base import BaseState

@dataclass
class Acmd41Response:
    base: BaseMsg
    busy: bool
    ccs: bool
    uhsii: bool
    s18a: bool
    ocr: OCRVoltageWindow

    def __init__(self, base: BaseMsg):
        self.base = base
        self.busy = (base.payload >> 31) & 1 != 0
        self.ccs = (base.payload >> 30) & 1 != 0
        self.uhsii = (base.payload >> 29) & 1 != 0
        self.s18a = (base.payload >> 24) & 1 != 0
        self.ocr = OCRVoltageWindow(((base.payload >> 8) & 0xFFFF) << 8)

class SendACmd41(BaseState):
    def __init__(self, inquiry: bool):
        super().__init__()
        self.inquiry = inquiry

    async def on_message(self, m: BaseMsg, iface: MmcInterface):
        # If this is a response to the CMD55
        if m.cmd == SDCommand.CMD55.value:
            msg = R1Response(m)
            print(msg)
            if not msg.base.crc_valid():
                raise MmcError("CMD55 response has incorrect CRC value")
            if not msg.status.app_cmd:
                raise MmcError("CMD55 response didn't set app cmd flag")
            # Send ACMD41
            if self.inquiry:
                # Send a payload of 0 to perform an inquiry
                await iface.write_cmd_send_bcr_48(build_acmd41(hcs=False, xpc=False, voltage=0))
            else:
                # busy=0 | hcs(1) | fb=0 | xpc(1) | 3.3v-3.4v(1) | 3.2v_3.3v (1)
                await iface.write_cmd_send_bcr_48(build_acmd41(hcs=True, xpc=True, voltage=0b0011000000000000))
        # If this is the response to the ACMD
        elif m.cmd == 63:
            msg = Acmd41Response(m)
            print(msg)
            if msg.base.crc != 0x7f:
                raise MmcError("ACMD41 response has incorrect CRC value")

            if self.inquiry:
                iface.ocr = msg.ocr
                iface.ccs = msg.ccs
                iface.uhsii = msg.uhsii
                iface.s18a = msg.s18a
                return True

            # If not busy, card isn't ready, we need to retry
            if msg.busy:
                # Go to next state, card is ready
                return True
            else:
                # Retry
                await iface.write_cmd_send_bcr_48(build_cmd55(rca=0))

    async def on_new_state(self, iface: MmcInterface):
        # Because this is an ACMD, we have to send cmd55 first
        await iface.write_cmd_send_bcr_48(build_cmd55(rca=0))