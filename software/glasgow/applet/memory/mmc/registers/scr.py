from dataclasses import dataclass


# TODO: scr or csr?
@dataclass
class CSRRegister:
    crc: int
    scr_struct: int
    sd_spec: int
    data_stat_after_erase: int
    sd_security: int
    sd_bus_widths: int
    sd_spec3: int
    ex_security: int
    sd_spec4: int
    sd_specx: int
    cmd_support: int

    def __init__(self, v: int):
        self.crc = v & 0x7FFF

        scr = v >> 15
        self.scr_struct = (scr >> 60) & 0xF
        self.sd_spec = (scr >> 56) & 0xF
        self.data_stat_after_erase = (scr >> 55) & 1 != 0
        self.sd_security = (scr >> 52) & 0b111
        self.sd_bus_widths = (scr >> 48) & 0xF
        self.sd_spec3 = (scr >> 47) & 1 != 0
        self.ex_security = (scr >> 43) & 0xF
        self.sd_spec4 = (scr >> 42) & 1 != 0
        self.sd_specx = (scr >> 38) & 0xF
        self.cmd_support = (scr >> 32) & 0xF