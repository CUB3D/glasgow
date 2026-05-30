from enum import Enum


class CardState(Enum):
    Idle = 0
    Ready = 1
    Ident = 2
    Stby = 3
    Tran = 4
    Data = 5
    Rcv = 6
    Prg = 7
    Dis = 8

    Unknown = 0xFF

    @classmethod
    def _missing_(self, key):
        return self.Unknown