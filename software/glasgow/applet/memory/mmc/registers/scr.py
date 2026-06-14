from dataclasses import dataclass

@dataclass
class SdSecurity:
    val: int

    def __init__(self, val: int):
        self.val = val

    def description(self):
        if self.val == 0:
            return "No Security"
        elif self.val == 1:
            return "Not Used"
        elif self.val == 2:
            return "SDSC Card (Security Version 1.01)"
        elif self.val == 3:
            return "SDHC Card (Security Version 2.00)"
        elif self.val == 4:
            return "SDXC Card (Security Version 3.xx)"
        else:
            return f"Reserved ({self.val})"

@dataclass
class SCRRegister:
    raw: int

    crc: int
    scr_struct: int
    sd_spec: int
    data_stat_after_erase: int
    sd_security: SdSecurity
    sd_bus_widths: int
    sd_spec3: int
    ex_security: int
    sd_spec4: int
    sd_specx: int
    cmd_support: int

    def __init__(self, v: int):
        self.raw = v
        self.crc = v & 0x7FFF

        scr = v >> 15
        self.scr_struct = (scr >> 60) & 0xF
        self.sd_spec = (scr >> 56) & 0xF
        self.data_stat_after_erase = (scr >> 55) & 1 != 0
        self.sd_security = SdSecurity((scr >> 52) & 0b111)
        self.sd_bus_widths = (scr >> 48) & 0xF
        self.sd_spec3 = (scr >> 47) & 1
        self.ex_security = (scr >> 43) & 0xF
        self.sd_spec4 = (scr >> 42) & 1
        self.sd_specx = (scr >> 38) & 0xF
        self.cmd_support = (scr >> 32) & 0xF

    def physical_spec_version(self):
        return {
            (0, 0, 0, 0): "Version 1.0 and 1.01",
            (1, 0, 0, 0): "Version 1.10",
            (2, 0, 0, 0): "Version 2.00",
            (2, 1, 0, 0): "Version 3.0X",
            (2, 1, 1, 0): "Version 4.XX",

            (2, 1, 0, 1): "Version 5.XX",
            (2, 1, 1, 1): "Version 5.XX",

            (2, 1, 0, 2): "Version 6.XX",
            (2, 1, 1, 2): "Version 6.XX",
        }.get(
            (self.sd_spec, self.sd_spec3, self.sd_spec4, self.sd_specx),
            f"Reserved ({self.sd_spec, self.sd_spec3, self.sd_spec4, self.sd_specx})"
        )
