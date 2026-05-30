from dataclasses import dataclass

from glasgow.applet.control.emmc.card_state import CardState


@dataclass
class CardStatus:
    ake_seq_error: bool
    app_cmd: bool
    fx_event: bool
    ready_for_data: bool
    current_state: CardState
    erase_reset: bool
    card_ecc_disabled: bool
    wp_erase_skip: bool
    csd_overwrite: bool
    error: bool
    cc_error: bool
    card_ecc_failed: bool
    illegal_command: bool
    com_crc_error: bool
    lock_unlock_failed: bool
    card_is_locked: bool
    wp_violation: bool
    erase_param: bool
    erase_seq_error: bool
    block_len_error: bool
    address_error: bool
    out_of_range: bool

    """
    Represent the Card Status field as defined in Table 4-42
    """
    def __init__(self, val: int):
        self.ake_seq_error = (val >> 3) & 1 != 0
        self.app_cmd = (val >> 5) & 1 != 0
        self.fx_event = (val >> 6) & 1 != 0
        self.ready_for_data = (val >> 8) & 1 != 0
        self.current_state = CardState((val >> 9) & 0b1111)
        self.erase_reset = (val >> 13) & 1 != 0
        self.card_ecc_disabled = (val >> 14) & 1 != 0
        self.wp_erase_skip = (val >> 15) & 1 != 0
        self.csd_overwrite = (val >> 16) & 1 != 0
        self.error = (val >> 19) & 1 != 0
        self.cc_error = (val >> 20) & 1 != 0
        self.card_ecc_failed = (val >> 21) & 1 != 0
        self.illegal_command = (val >> 22) & 1 != 0
        self.com_crc_error = (val >> 23) & 1 != 0
        self.lock_unlock_failed = (val >> 24) & 1 != 0
        self.card_is_locked = (val >> 25) & 1 != 0
        self.wp_violation = (val >> 26) & 1 != 0
        self.erase_param = (val >> 27) & 1 != 0
        self.erase_seq_error = (val >> 28) & 1 != 0
        self.block_len_error = (val >> 29) & 1 != 0
        self.address_error = (val >> 30) & 1 != 0
        self.out_of_range = (val >> 31) & 1 != 0