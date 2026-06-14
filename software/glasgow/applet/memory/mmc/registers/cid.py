from dataclasses import dataclass

@dataclass
class ManufacturingDate:
    month: int
    year: int

    def __init__(self, v: int):
        self.month = v & 0xF
        self.year = (v >> 4) + 2000

@dataclass
class ManufacturerId:
    id: int

    def __init__(self, id: int):
        self.id = id

    def __str__(self):
        if self.id == 1:
            return "Panasonic"
        elif self.id == 2:
            return "Toshiba"
        elif self.id == 3:
            return "Sandisk"
        elif self.id == 0x1b:
            return "Samsung"
        elif self.id == 0x1d:
            return "AData"
        elif self.id == 0x27:
            return "Phison"
        elif self.id == 0x28:
            return "Lexar"
        elif self.id == 0x41:
            return "Kingston"
        elif self.id == 0x74:
            return "Transcend"
        elif self.id == 0x82:
            return "Sony"
        elif self.id == 0xC9:
            return "Kodak"
        else:
            return f"Unknown ({self.id})"

@dataclass
class ProductRevision:
    major: int
    minor: int

    def __init__(self, v: int):
        self.major = v >> 4
        self.minor = v & 0xF

@dataclass
class CIDRegister:
    raw: int

    mid: ManufacturerId
    oem: str
    pnm: str
    prv: ProductRevision
    psn: int
    mdt: ManufacturingDate
    crc: int

    def __init__(self, v: int):
        self.raw = v
        self.mid = ManufacturerId((v >> 120) & 0xFF)
        oem = (v >> 104) & 0xFFFF
        self.oem = chr(oem >> 8) + chr(oem & 0xFF)
        pnm = (v >> 64) & 0xFF_FFFF_FFFF
        self.pnm = chr((pnm >> 32) & 0xff) + chr((pnm >> 24) & 0xff) + chr((pnm >> 16) & 0xff) + chr(
            (pnm >> 8) & 0xFF) + chr(pnm & 0xFF)
        self.prv = ProductRevision((v >> 56) & 0xFF)
        self.psn = (v >> 24) & 0xFFFF_FFFF
        self.mdt = ManufacturingDate((v >> 8) & 0xFFF)
        self.crc = (v >> 1) & 0x1111111

