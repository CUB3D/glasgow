from dataclasses import dataclass
from typing import Optional

@dataclass
class CSDRegister:
    csd_structure: int
    taac: int
    nsac: int
    tran_speed: int
    ccc: int
    read_bl_len: int
    read_bl_partial: bool
    write_blk_misalign: bool
    read_blk_misalign: bool
    dsr_imp: bool
    c_size: int
    vdd_r_curr_min: Optional[int]
    vdd_r_curr_max: Optional[int]
    vdd_w_curr_min: Optional[int]
    vdd_w_curr_max: Optional[int]
    c_size_mult: Optional[int]
    erase_blk_en: bool
    sector_size: int
    wp_grp_size: int
    wp_grp_enable: bool
    r2w_factor: int
    write_bl_len: int
    write_bl_partial: bool
    file_format_grp: bool
    copy: int
    perm_write_protect: bool
    tmp_write_protect: bool
    file_format: int
    crc: int

    def __init__(self, x: int):
        self.csd_structure = (x >> 126) & 0b11

        # Common
        self.taac = (x >> 112) & 0xFF
        self.nsac = (x >> 104) & 0xFF
        self.tran_speed = (x >> 96) & 0xFF
        self.ccc = (x >> 84) & 0xFFF
        self.read_bl_len = (x >> 80) & 0xF
        self.read_bl_partial = (x >> 79) & 1 != 0
        self.write_blk_misalign = (x >> 78) & 1 != 0
        self.read_blk_misalign = (x >> 77) & 1 != 0
        self.dsr_imp = (x >> 76) & 1 != 0

        self.erase_blk_en = (x >> 46) & 1 != 0
        self.sector_size = (x >> 39) & 0b1111111
        self.wp_grp_size = (x >> 32) & 0b1111111
        self.wp_grp_enable = (x >> 31) & 1 != 0
        self.r2w_factor = (x >> 26) & 0b111
        self.write_bl_len = (x >> 22) & 0xF
        self.write_bl_partial = (x >> 21) & 1 != 0
        self.file_format_grp = (x >> 15) & 1 != 0
        self.copy = (x >> 14) & 1 != 0
        self.perm_write_protect = (x >> 13) & 1 != 0
        self.tmp_write_protect = (x >> 12) & 1 != 0
        self.file_format = (x >> 10) & 0b11
        self.crc = (x >> 1) & 0b1111111

        # Version 1.0
        if self.csd_structure == 0:
            self.c_size = (x >> 62) & 0xFFF
            self.vdd_r_curr_min = (x >> 59) & 0b111
            self.vdd_r_curr_max = (x >> 56) & 0b111
            self.vdd_w_curr_min = (x >> 53) & 0b111
            self.vdd_w_curr_max = (x >> 50) & 0b111
            self.c_size_mult = (x >> 47) & 0b111

        # Version 2.0
        elif self.csd_structure == 1:
            self.c_size = (x >> 48) & 0b11111111_11111111_111111
            self.vdd_r_curr_min = None
            self.vdd_r_curr_max = None
            self.vdd_w_curr_min = None
            self.vdd_w_curr_max = None
            self.c_size_mult = None

    def get_capacity_v1(self):
        blklen = 2 ** self.read_bl_len
        mult = 2 ** (self.c_size_mult + 2)
        blknr = (self.c_size + 1) * mult
        return blklen + blknr * blklen

    def get_capacity_v2(self):
        return (self.c_size + 1) * 512 * 1024

    def get_capacity(self):
        if self.csd_structure == 0:
            return self.get_capacity_v1()
        elif self.csd_structure == 1:
            return self.get_capacity_v2()
        return None