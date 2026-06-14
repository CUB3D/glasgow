import itertools
from amaranth import *
from amaranth.sim import SimulatorContext

from glasgow.applet import GlasgowAppletTestCase, applet_simulation_test, synthesis_test
from . import MemoryMmcApplet


class MemoryMmcAppletTestCase(GlasgowAppletTestCase, applet=MemoryMmcApplet):
    @synthesis_test
    def test_build_opl2(self):
        self.assertBuilds(args=["--clk", "A0", "--cmd", "A1", "--vcc", "A2", "--dat0", "A3", "--test", "A4"])

    def prepare_target(self, target, parsed_args):
        # target.assembly.sys_clk_period = lambda x: 1/1000000000
        self.applet.build(target, parsed_args)

    @applet_simulation_test(setup="prepare_target", args=["--clk", "A0", "--cmd", "A1", "--vcc", "A2", "--dat0", "A3", "--test", "A4"])
    async def test_loopback(self, device, parsed_args, ctx):
        await self.applet.run(device, parsed_args)
        await ctx.tick().repeat(100000)
        exit()
