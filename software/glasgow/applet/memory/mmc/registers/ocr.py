from dataclasses import dataclass


@dataclass
class OCRVoltageWindow:
    v27_28: bool
    v28_29: bool
    v29_30: bool
    v30_31: bool
    v31_32: bool
    v32_33: bool
    v33_34: bool
    v34_35: bool
    v35_36: bool

    def __init__(self, v: int):
        self.v27_28 = (v >> 15) & 1 != 0
        self.v28_29 = (v >> 16) & 1 != 0
        self.v29_30 = (v >> 17) & 1 != 0
        self.v30_31 = (v >> 18) & 1 != 0
        self.v31_32 = (v >> 19) & 1 != 0
        self.v32_33 = (v >> 20) & 1 != 0
        self.v33_34 = (v >> 21) & 1 != 0
        self.v34_35 = (v >> 22) & 1 != 0
        self.v35_36 = (v >> 23) & 1 != 0


