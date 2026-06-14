# Support for accessing SD/{e}MMC devices in SD mode
# https://www.taterli.com/wp-content/uploads/2017/05/Physical-Layer-Simplified-SpecificationV6.0.pdf

import logging
from dataclasses import dataclass
from typing import List

import amaranth
from amaranth import *
from amaranth.lib import io
from amaranth.lib.data import Struct
from amaranth.lib.fifo import SyncFIFO
from amaranth.lib.io import Direction
from amaranth.lib.memory import WritePort, Memory

from glasgow.applet.memory.mmc.registers.ocr import OCRVoltageWindow
from .base_msg import BaseMsg
from .cmd import build_cmd0, reverse_bits, crc7, build_cmd8
from .interface import MmcInterface, IN_CMD_SEND_BCR48, IN_CMD_SEND_BCR136, IN_CMD_SEND_DATA48, IN_CMD_FILL_BUFFER, \
    IN_CMD_READ_BUFFER, IN_CMD_RESET
from .registers.cid import CIDRegister
from .state.base import BaseState
from .state.send_acmd41 import SendACmd41
from .state.send_acmd51 import SendACmd51
from .state.send_cmd16 import SendCmd16
from .state.send_cmd17 import SendCmd17
from .state.send_cmd2 import SendCmd2
from .state.send_cmd3 import SendCmd3
from .state.send_cmd7 import SendCmd7
from .state.send_cmd8 import SendCmd8
from ... import GlasgowApplet
from ....gateware.clockgen import *
from ....legacy import DeprecatedTarget
from ....support.data_logger import DataLogger


# TODO: test on actual emmc
# TODO: extended regs
# Refactor cmd builder
# Add erase subcommand
# read subcommand addr and size
# Clean up cmd structure
# Multiple gpios for vcc current
# response timeouts

class MmcPkt(Struct):
    cmd: 50 #TODO: why 50, not 48
    has_resp: 1
    resp_size: 1
    has_data: 1

def mk_bc(cmd):
    return Signal(MmcPkt, init={"cmd": cmd, "has_resp": 0, "resp_size": 0, "has_data": 0}).as_value()

def mk_bcr(cmd, resp_length=48):
    return Signal(MmcPkt, init={"cmd": cmd, "has_resp": 1, "resp_size": resp_length == 136, "has_data": 0}).as_value()

# def get_acmd6():
#     cmd8_part1 = 0b0 \
#                  | (1 << 1) \
#                  | (reverse_bits(0b000110, 6) << 2) \
#                  | (reverse_bits(0x0000_0003, 32) << 8)
#
#     crc = crc7(reverse_bits(cmd8_part1, 40).to_bytes(5, byteorder="big"))
#
#     cmd8_full = cmd8_part1 \
#                 | (reverse_bits(crc, 7) << 40) \
#                 | (1 << 47)
#
#     return cmd8_full

import random

# CLK_HZ = 100+5*13

CLK_HZ = 5 * random.randint(20, 100)
print(CLK_HZ)

CLK_HZ=700
# CLK_HZ=375
# CLK_HZ=450

# def get_cmd9(rca):
#     """
#     SEND_CSD
#     """
#     cmd_no_crc = 0b0 \
#                  | (1 << 1) \
#                  | (reverse_bits(0b001001, 6) << 2) \
#                  | (reverse_bits(rca << 16, 32) << 8)
#
#     crc = crc7(reverse_bits(cmd_no_crc, 40).to_bytes(5, byteorder="big"))
#
#     cmd = cmd_no_crc \
#                 | (reverse_bits(crc, 7) << 40) \
#                 | (1 << 47)
#
#     return cmd

class MmcHelper(Elaboratable):
    queue: SyncFIFO
    done: Signal
    err: Signal

    can_output: Signal
    cmd_en: Signal
    cmd_out: Signal
    in_cmd_buffer: io.Buffer
    in_fifo: SyncFIFO

    dat0_en: Signal
    dat1_en: Signal
    dat2_en: Signal
    dat3_en: Signal
    in_dat0_buffer: io.Buffer

    data_buffer_wr_port: WritePort

    def __init__(self):
        self.queue = SyncFIFO(width=Signal(MmcPkt).as_value().shape().width, depth=4)
        self.done = Signal(1, init=0)
        self.err = Signal(1, init=0)

    """
    Handles MMC IO
    takes in requests, sends them, waits for responses if required and provides them
    """
    def elaborate(self, platform):
        m = Module()
        m.submodules.queue = self.queue

        pkt_req = Signal(MmcPkt, init=0)
        counter = Signal(8, init=0) # max = 136
        tmp = Signal(8, init=0)
        count = Signal(3, init=0)

        data_state = Signal(3, init=0)
        data_count = Signal(3, init=0)
        data_counter = Signal(16, init=0)
        data_out = Signal(8, init=0)

        with m.If(self.can_output):
            with m.FSM():
                # Wait for request to send a packet
                with m.State("DEQUEUE"):
                    m.d.sync += counter.eq(0)
                    m.d.comb += self.queue.r_en.eq(1)
                    with m.If(self.queue.r_rdy):
                        m.d.sync += pkt_req.eq(self.queue.r_data)
                        
                        m.d.sync += self.done.eq(0)
                        m.d.sync += self.err.eq(0)
                        m.d.sync += self.dat0_en.eq(0)
                        m.d.sync += self.dat1_en.eq(0)
                        m.d.sync += self.dat2_en.eq(0)
                        m.d.sync += self.dat3_en.eq(0)
                        m.next = "CMD_OUT"
                with m.State("CMD_OUT"):
                    m.d.sync += self.cmd_en.eq(1)
                    with m.If(counter < 48): # while we still have bits to output
                        m.d.sync += counter.eq(counter + 1)
                        m.d.sync += self.cmd_out.eq(pkt_req.cmd & 1) # output LSB
                        m.d.sync += pkt_req.cmd.eq(pkt_req.cmd >> 1) # shift lsb
                    with m.Else():
                        # TODO: I don't know why this is off, but it seems connected to freq?
                        with m.If(pkt_req.resp_size):
                            m.d.sync += counter.eq(7-2)
                        with m.Else():
                            m.d.sync += counter.eq(7-3)

                        m.next = "PKT_END"

                # Mark the end of packet by keeping the line pulled high
                with m.State("PKT_END"):
                    # Start waiting for resp on data lines if this command has data response
                    with m.If(pkt_req.has_data):
                        # m.d.sync += self.dat0_en.eq(0)
                        # m.d.sync += self.dat1_en.eq(0)
                        # m.d.sync += self.dat2_en.eq(0)
                        m.d.sync += data_state.eq(1)

                    with m.If(counter > 0):
                        m.d.sync += counter.eq(counter - 1)
                    with m.Else():
                        # Release CMD, wait up to 64 cycles for a 0 on CMD
                        m.d.sync += counter.eq(64)
                        m.d.sync += self.cmd_en.eq(0)
                        m.next = "DELAY"

                with m.State("DELAY"):
                    # If we don't expect a resp, goto DEQUEUE
                    with m.If(~pkt_req.has_resp):
                        m.d.sync += self.done.eq(1)
                        m.next = "DEQUEUE"
                    with m.Else():
                        # If we read a 0 on CMD, start of packet
                        with m.If(~self.in_cmd_buffer.i):
                            with m.If(~pkt_req.resp_size):
                                # This is a 48 bit cmd
                                m.d.comb += self.in_fifo.w_data.eq(0xa1)
                                m.d.comb += self.in_fifo.w_en.eq(1)
                                # Read 48 bits, starting from 1, (already read the first 0)
                                m.d.sync += counter.eq(48-1)
                            with m.Else():
                                # This is a 136 bit cmd
                                m.d.comb += self.in_fifo.w_data.eq(0xa3)
                                m.d.comb += self.in_fifo.w_en.eq(1)
                                # Read 136 bits, starting from 1, (already read the first 0)
                                m.d.sync += counter.eq(136-1)

                            # goto READ
                            m.next = "READ"
                            m.d.sync += tmp.eq(0)
                            m.d.sync += count.eq(1)
                        with m.Else():
                            # Count down timeout counter, if expires, goto ERR
                            with m.If(counter > 0):
                                m.d.sync += counter.eq(counter - 1)
                            with m.Else():
                                m.next = "ERR"

                with m.State("READ"):
                    with m.If(counter > 0):
                        m.d.sync += counter.eq(counter - 1)
                        m.d.sync += count.eq(count + 1)
                        m.d.sync += tmp.eq((tmp << 1) | self.in_cmd_buffer.i)
                        with m.If(count == 7):
                            m.d.comb += self.in_fifo.w_data.eq(tmp)
                            m.d.comb += self.in_fifo.w_en.eq(1)
                            m.d.sync += count.eq(0)
                    with m.Else():
                        m.d.sync += counter.eq(45)
                        m.next = "PAUSE"

                # Wait for a few cycles before completing next command
                with m.State("PAUSE"):
                    with m.If(counter > 0):
                        m.d.sync += counter.eq(counter - 1)
                    with m.Else():
                        # Flag as done, if this command has a data resp then wait for the data read to finish first
                        with m.If(pkt_req.has_data): # If we have data
                            with m.If(data_state == 0): # If the data read is done, next cmd
                                m.d.sync += self.done.eq(1)
                                m.next = "DEQUEUE"
                        with m.Else(): # No data, next cmd
                            m.d.sync += self.done.eq(1)
                            m.next = "DEQUEUE"

                with m.State("ERR"):
                    m.d.sync += self.err.eq(1)
                    m.d.sync += self.done.eq(0)
                    m.next = "DEQUEUE"

            # Data read state machine
            # Waiting for 0
            with m.If(data_state == 1):
                # Wait for dat0 to go low
                with m.If(~self.in_dat0_buffer.i):
                    m.d.sync += data_counter.eq(512+16) # Block size, 512 *bytes*
                    m.d.sync += data_state.eq(2)
                    m.d.sync += data_count.eq(0)
                    m.d.sync += data_out.eq(0)

                    m.d.comb += self.in_fifo.w_data.eq(0xFF)
                    m.d.comb += self.in_fifo.w_en.eq(1)
            # Reading
            with m.Elif(data_state == 2):
                with m.If(data_counter > 0):
                    m.d.sync += data_out.eq((data_out << 1) | self.in_dat0_buffer.i)
                    m.d.sync += data_count.eq(data_count + 1)
                    with m.If(data_count == 7):
                        # m.d.sync += self.data_buffer_wr_port.addr.eq(self.data_buffer_wr_port.addr + 1)
                        # m.d.comb += self.data_buffer_wr_port.en.eq(1)
                        # m.d.comb += self.data_buffer_wr_port.data.eq(data_out)

                        m.d.comb += self.in_fifo.w_data.eq(data_out)
                        m.d.comb += self.in_fifo.w_en.eq(1)

                        m.d.sync += data_counter.eq(data_counter - 1)
                        m.d.sync += data_count.eq(0)
                with m.Else():
                    m.d.sync += data_state.eq(0)
                    # m.d.sync += self.dat0_en.eq(1)
                    # m.d.sync += self.dat1_en.eq(1)
                    # m.d.sync += self.dat2_en.eq(1)
            # with m.Elif(data_state == 3):
            #     with m.If(self.data_buffer_rd_port.addr == 511):
            #         m.d.sync += self.data_buffer_rd_port.addr.eq(0)
            #         m.d.sync += data_state.eq(4)
            #     with m.Else():
            #         m.d.comb += self.in_fifo.w_data.eq(self.data_buffer_rd_port.data)
            #         m.d.comb += self.in_fifo.w_en.eq(1)
            #
            #         m.d.sync += self.data_buffer_rd_port.addr.eq(self.data_buffer_rd_port.addr + 1)





        return m


class SensorMmcSubtarget(Elaboratable):
    def __init__(self, ports, osc_cyc, in_fifo, out_fifo):
        self.ports    = ports
        self.osc_cyc  = osc_cyc
        self.in_fifo = in_fifo
        self.out_fifo = out_fifo

    def elaborate(self, platform):
        m = Module()

        m.submodules.helper = MmcHelper()


        m.submodules.clkgen = clkgen = ClockGen(self.osc_cyc)
        m.submodules.clk_buffer = clk_buffer = io.Buffer(Direction.Output, self.ports.clk)
        m.submodules.cmd_buffer = cmd_buffer = io.Buffer(Direction.Bidir, self.ports.cmd)
        m.submodules.dat0_buffer = dat0_buffer = io.Buffer(Direction.Bidir, self.ports.dat0)
        m.submodules.dat1_buffer = dat1_buffer = io.Buffer(Direction.Bidir, self.ports.dat1)
        m.submodules.dat2_buffer = dat2_buffer = io.Buffer(Direction.Bidir, self.ports.dat2)
        m.submodules.dat3_buffer = dat3_buffer = io.Buffer(Direction.Bidir, self.ports.dat3)

        sleep = Signal(8, init=0, name="sleep")
        cmd = Signal(1, init=1)
        dat0 = Signal(1, init=1)
        dat1 = Signal(1, init=1)
        dat2 = Signal(1, init=1)
        dat3 = Signal(1, init=1)

        # Detect change in clock
        tmpclk = Signal(1, init=0, name="tmpclk")
        clk_edge = Signal(1, init=0)
        m.d.sync += tmpclk.eq(clkgen.clk)
        m.d.comb += clk_edge.eq(tmpclk != clkgen.clk)

        can_output = Signal(1, init=0)
        m.d.comb += can_output.eq(clk_edge & (tmpclk == 1))


        # On a clock edge that was previously pos i.e. negative edge
        m.d.comb += clk_buffer.o.eq(clkgen.clk)

        cmd_en = Signal(1, init=1)
        dat0_en = Signal(1, init=1)
        dat1_en = Signal(1, init=1)
        dat2_en = Signal(1, init=1)
        dat3_en = Signal(1, init=1)

        m.d.comb += cmd_buffer.o.eq(cmd)
        m.d.comb += cmd_buffer.oe.eq(cmd_en)

        m.d.comb += dat0_buffer.o.eq(dat0)
        m.d.comb += dat0_buffer.oe.eq(dat0_en)

        m.d.comb += dat1_buffer.o.eq(dat1)
        m.d.comb += dat1_buffer.oe.eq(dat1_en)

        m.d.comb += dat2_buffer.o.eq(dat2)
        m.d.comb += dat2_buffer.oe.eq(dat2_en)

        m.d.comb += dat3_buffer.o.eq(dat3)
        m.d.comb += dat3_buffer.oe.eq(dat3_en)

        m.submodules.helper.can_output = can_output
        m.submodules.helper.cmd_out = cmd
        m.submodules.helper.in_fifo = self.in_fifo
        m.submodules.helper.in_cmd_buffer = cmd_buffer
        m.submodules.helper.in_dat0_buffer = dat0_buffer
        m.submodules.helper.cmd_en = cmd_en
        m.submodules.helper.dat0_en = dat0_en
        m.submodules.helper.dat1_en = dat1_en
        m.submodules.helper.dat2_en = dat2_en
        m.submodules.helper.dat3_en = dat3_en

        # m.submodules.data_buffer = data_buffer = amaranth.lib.memory.Memory(shape=unsigned(8), depth=32, init=[0] * 32)
        # data_buffer_wr_port = data_buffer.write_port()

        # m.submodules.helper.data_buffer_wr_port = data_buffer.write_port()
        # m.submodules.helper.data_buffer_rd_port = data_buffer.read_port(domain="comb")

        arg_cnt = Signal(3, init=0)

        in_cmd = Signal(8, init=0)
        in_arg = Signal(48, init=0)

        with m.If(clk_edge & (tmpclk == 1)):
            with m.FSM("POWER_OFF"):
                with m.State("POWER_OFF"):
                    m.d.sync += sleep.eq(254)  # 1ms + 74 clk should be
                    m.d.sync += dat0.eq(1)
                    m.next = "SLEEP"
                with m.State("SLEEP"):
                    with m.If(sleep > 0):
                        m.d.sync += sleep.eq(sleep - 1)
                    with m.Else():
                        m.d.sync += dat0.eq(0)
                        m.next = "CMD0_SEND"
                with m.State("CMD0_SEND"):
                    m.d.comb += m.submodules.helper.queue.w_en.eq(1)
                    m.d.comb += m.submodules.helper.queue.w_data.eq(
                        mk_bc(build_cmd0())
                    )
                    m.next = "CMD0_WAIT"
                with m.State("CMD0_WAIT"):
                    # no resp, can't error
                    with m.If(m.submodules.helper.done):
                        m.next = "CMD8_SEND"

                with m.State("CMD8_SEND"):
                    m.d.comb += m.submodules.helper.queue.w_en.eq(1)
                    m.d.comb += m.submodules.helper.queue.w_data.eq(
                        mk_bcr(build_cmd8())
                    )
                    m.next = "CMD8_WAIT"

                with m.State("CMD8_WAIT"):
                    with m.If(m.submodules.helper.done):
                        m.next = "WAIT4CMD"
                    with m.If(m.submodules.helper.err):
                        m.next = "POWER_OFF"

                with m.State("WAIT4CMD"):
                    with m.If(self.out_fifo.r_rdy):
                        m.d.comb += self.out_fifo.r_en.eq(1)
                        m.d.sync += in_cmd.eq(self.out_fifo.r_data)
                        m.d.sync += arg_cnt.eq(0)
                        m.d.sync += in_arg.eq(0)
                        m.next = "CMD_ARG"
                with m.State("CMD_ARG"):
                    with m.If(arg_cnt < 6):
                        with m.If(self.out_fifo.r_rdy):
                            m.d.comb += self.out_fifo.r_en.eq(1)
                            m.d.sync += in_arg.eq((in_arg << 8) | self.out_fifo.r_data)
                            m.d.sync += arg_cnt.eq(arg_cnt+1)
                    with m.Else():
                        m.next = "CMD_PROC"
                with m.State("CMD_PROC"):
                    temp_phy_cmd = Signal(MmcPkt)


                    with m.If(in_cmd == IN_CMD_SEND_BCR48):
                        m.d.comb += temp_phy_cmd.cmd.eq(in_arg)
                        m.d.comb += temp_phy_cmd.has_resp.eq(1)
                        m.d.comb += temp_phy_cmd.resp_size.eq(0)
                        m.d.comb += temp_phy_cmd.has_data.eq(0)

                        m.d.comb += m.submodules.helper.queue.w_en.eq(1)
                        m.d.comb += m.submodules.helper.queue.w_data.eq(temp_phy_cmd)
                        m.next = "CMD_WAIT"
                    with m.Elif(in_cmd == IN_CMD_SEND_BCR136):
                        m.d.comb += temp_phy_cmd.cmd.eq(in_arg)
                        m.d.comb += temp_phy_cmd.has_resp.eq(1)
                        m.d.comb += temp_phy_cmd.resp_size.eq(1)
                        m.d.comb += temp_phy_cmd.has_data.eq(0)

                        m.d.comb += m.submodules.helper.queue.w_en.eq(1)
                        m.d.comb += m.submodules.helper.queue.w_data.eq(temp_phy_cmd)
                        m.next = "CMD_WAIT"
                    with m.Elif(in_cmd == IN_CMD_SEND_DATA48):
                        m.d.comb += temp_phy_cmd.cmd.eq(in_arg)
                        m.d.comb += temp_phy_cmd.has_resp.eq(1)
                        m.d.comb += temp_phy_cmd.resp_size.eq(0)
                        m.d.comb += temp_phy_cmd.has_data.eq(1)

                        m.d.comb += m.submodules.helper.queue.w_en.eq(1)
                        m.d.comb += m.submodules.helper.queue.w_data.eq(temp_phy_cmd)
                        m.next = "CMD_WAIT"
                    with m.Elif(in_cmd == IN_CMD_RESET):
                        m.next = "POWER_OFF"
                    # with m.Elif(in_cmd == IN_CMD_FILL_BUFFER):
                    #     m.d.sync += data_buffer_wr_port.addr.eq(0)
                    #     m.next = "CMD_BUFFER_FILL"
                    # with m.Elif(in_cmd == IN_CMD_READ_BUFFER):
                    #     m.d.sync += data_buffer_rd_port.addr.eq(0)
                    #     m.next = "CMD_BUFFER_READ"
                    with m.Else():
                        m.next = "CMD_WAIT"
                with m.State("CMD_WAIT"):
                    with m.If(m.submodules.helper.done):
                        m.next = "WAIT4CMD"


                # with m.State("CMD_BUFFER_FILL"):
                #     # Read in 512 bytes from the fifo, into data_buffer
                #     with m.If(data_buffer_wr_port.addr == data_buffer.depth - 1):
                #         m.d.sync += data_buffer_wr_port.addr.eq(0)
                #         m.next = "WAIT4CMD"
                #     with m.Else():
                #         with m.If(self.out_fifo.r_rdy):
                #             m.d.comb += self.out_fifo.r_en.eq(1)
                #
                #             m.d.comb += data_buffer_wr_port.data.eq(self.out_fifo.r_data)
                #             m.d.comb += data_buffer_wr_port.en.eq(1)
                #             m.d.sync += data_buffer_wr_port.addr.eq(data_buffer_wr_port.addr + 1)

                # with m.State("CMD_BUFFER_READ"):
                #     # Write out 512 bytes from data_buffer, into the fifo
                #     with m.If(data_buffer_rd_port.addr == data_buffer.depth - 1):
                #         m.d.sync += data_buffer_rd_port.addr.eq(0)
                #         m.next = "WAIT4CMD"
                #     with m.Else():
                #         with m.If(self.in_fifo.w_rdy):
                #             m.d.comb += self.in_fifo.w_en.eq(1)
                #             m.d.comb += self.in_fifo.w_data.eq(data_buffer_rd_port.data)
                #             m.d.sync += data_buffer_rd_port.addr.eq(data_buffer_rd_port.addr + 1)


        return m

#TODO: cmd 1 refactor
"""
Command structure

id: u4
flags: u4

Commands:

send - 1
flags: has_data(0), has_resp(1)
takes 5 byte cmd as data

read buffer - 2

dump 512 byte buffer from last read


fill buffer - 3

take next 512 bytes and put in buffer
"""

class MemoryMmcApplet(GlasgowApplet):
    logger = logging.getLogger(__name__)
    help = ""
    description = """
    """

    @classmethod
    def add_build_arguments(cls, parser, access):
        super().add_build_arguments(parser, access)

        access.add_pins_argument(parser, "clk", required=True)
        access.add_pins_argument(parser, "cmd", required=True)
        access.add_pins_argument(parser, "vcc", required=True)
        access.add_pins_argument(parser, "dat0", required=True)
        access.add_pins_argument(parser, "dat1", required=True)
        access.add_pins_argument(parser, "dat2", required=True)
        access.add_pins_argument(parser, "dat3", required=True)

    def build(self, target: DeprecatedTarget, args):
        osc_cyc = self.derive_clock(clock_name="osc",input_hz=target.sys_clk_freq, output_hz=CLK_HZ)

        self.mux_interface = iface = target.multiplexer.claim_interface(self, args)
        subtarget = iface.add_subtarget(SensorMmcSubtarget(
            ports=iface.get_port_group(
                clk=args.clk,
                cmd=args.cmd,
                dat0=args.dat0,
                dat1=args.dat1,
                dat2=args.dat2,
                dat3=args.dat3,
            ),
            osc_cyc=osc_cyc,
            in_fifo=iface.get_in_fifo(),
            out_fifo=iface.get_out_fifo(),
        ))

    async def run(self, device, args):
        iface = await device.demultiplexer.claim_interface(self, self.mux_interface, args, pull_high={args.dat0, args.dat1, args.dat2, args.dat3, args.cmd})
        return MmcInterface(iface)

    @classmethod
    def tests(cls):
        from . import test
        return test.MemoryMmcAppletTestCase

    @classmethod
    def add_interact_arguments(cls, parser):
        p_operation = parser.add_subparsers(dest="operation", metavar="OPERATION", required=True)

        p_info = p_operation.add_parser("info", help="Get card info")
        DataLogger.add_subparsers(p_info)

        p_erase = p_operation.add_parser("erase", help="Erase card")
        DataLogger.add_subparsers(p_erase)

        p_read = p_operation.add_parser("read", help="Read card")
        DataLogger.add_subparsers(p_read)

    async def interact(self, device, args, iface):
        q = SDCommandQueue()
        q.add(SendCmd8())
        q.add(SendACmd41())
        q.add(SendCmd2())
        q.add(SendCmd3())
        q.add(SendCmd7())
        # q.add(SendACmd51())
        q.add(SendCmd16())
        q.add(SendCmd17())

        while True:
            typ = await iface.read_1()
            print("ty", hex(typ))
            if typ == 0xa1:
                x = await iface.read_5()

                m = BaseMsg(x)

                print("cmd", m.cmd, bin(m.cmd))
                print("payload", hex(m.payload), bin(m.payload))
                print("crc", hex(m.crc), bin(m.crc))
                print("Valid", "TRUE" if m.crc_valid() else "!FALSE!")

                print(", ".join([x for x in ("00000000" + bin(x)[2:])[-48:]]))

                await q.handle_msg(m, iface)

            if typ == 0xa2:
                x = await iface.read_1()
                print(", ".join([x for x in ("00000000" + bin(x)[2:])[-8:]]))

            # CMD2 resp
            if typ == 0xa3:
                x = await iface.read_17()
                y = BaseMsg(0)
                y.cmd = 2
                y.payload = x

                await q.handle_msg(y, iface)

            print("-----------")

#TODO: fallback values for enums



# TODO: state machine?
class SDCommandQueue:
    queue: List[BaseState]

    def __init__(self):
        self.queue = []
    
    def add(self, x: BaseState):
        self.queue.append(x)

    async def handle_msg(self, m: BaseMsg, iface: MmcInterface):
        print("q", self.queue[0], "m", m)
        res = await self.queue[0].on_message(m, iface)
        if res:
            self.queue.pop(0)
            await self.queue[0].on_new_state(iface)






