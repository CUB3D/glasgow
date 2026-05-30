# Ref: HX711 24-Bit Analog-to-Digital Converter (ADC) for Weigh Scales
# Accession: G00049

import logging
import asyncio
from amaranth import *
from amaranth.lib import io, cdc
from amaranth.lib.memory import Memory

from ... import *
from ....gateware.clockgen import *
from ....support.data_logger import DataLogger


class SensorJieliSubtarget(Elaboratable):
    def __init__(self, ports, osc_cyc):
        self.ports    = ports
        self.osc_cyc  = osc_cyc

    def elaborate(self, platform):
        m = Module()
        
        message = [0,0,0,1, 0,1,1,0, 1,1,1,0, 1,1,1,1]
        m.submodules.memory = memory = Memory(shape=unsigned(1), depth=len(message), init=message)
        rd_port = memory.read_port(domain="comb")
        

        m.submodules.clkgen = clkgen = ClockGen(self.osc_cyc)
        m.submodules.clk_buffer = clk_buffer = io.Buffer("o", self.ports.clk)
        m.submodules.data_buffer = data_buffer = io.Buffer("o", self.ports.data)


        
        # Detect change in clock
        tmpclk = Signal(1, init=0)
        clk_edge = Signal(1, init=0)
        m.d.sync += tmpclk.eq(clkgen.clk)
        m.d.comb += clk_edge.eq(tmpclk != clkgen.clk)

        # On a clock edge that was previously pos i.e. negative edge
        with m.If(clk_edge & (tmpclk == 1)):
            # Goto next memory cell, looping
            with m.If(rd_port.addr == memory.depth - 1):
                m.d.sync += rd_port.addr.eq(0)
            with m.Else():
                m.d.sync += rd_port.addr.eq(rd_port.addr + 1),
        
        # output clock and current memory cell
        m.d.comb += [
            clk_buffer.o.eq(clkgen.clk),
            data_buffer.o.eq(rd_port.data)
        ]

        return m

import time

class HX711Interface:
    def __init__(self, interface, logger):
        self._lower  = interface
        self._logger = logger
        self._level  = logging.TRACE

    def _log(self, message, *args):
        self._logger.log(self._level, "HX711: " + message, *args)

    async def sample(self):
        await self._lower.write([27])
        time.sleep(0.2)


class ControlJieliApplet(GlasgowApplet):
    logger = logging.getLogger(__name__)
    help = ""
    description = """
    """

    @classmethod
    def add_build_arguments(cls, parser, access):        
        super().add_build_arguments(parser, access)

        access.add_pins_argument(parser, "clk", required=True)
        access.add_pins_argument(parser, "data", required=True)

    def build(self, target, args):
        osc_cyc = self.derive_clock(clock_name="osc",input_hz=target.sys_clk_freq, output_hz=20000)#100)

        self.mux_interface = iface = target.multiplexer.claim_interface(self, args)
        iface.add_subtarget(SensorJieliSubtarget(
            ports=iface.get_port_group(
                clk=args.clk,
                data=args.data,
            ),
            osc_cyc=osc_cyc,
        ))

    async def run(self, device, args):
        iface = await device.demultiplexer.claim_interface(self, self.mux_interface, args)
        return HX711Interface(iface, self.logger)

    @classmethod
    def add_interact_arguments(cls, parser):
        p_operation = parser.add_subparsers(dest="operation", metavar="OPERATION", required=True)

        p_log = p_operation.add_parser("log", help="log measured values")
        DataLogger.add_subparsers(p_log)
        pass

    async def interact(self, device, args, hx711):
        data_logger = await DataLogger(self.logger, args, field_names={"n": "count(LSB)"})
        while True:
            sample = await hx711.sample()
            await data_logger.report_data(fields={"n": sample})
