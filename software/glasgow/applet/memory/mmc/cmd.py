def crc7(b: bytes):
    res = 0
    for byte in b:
        for idx in range(8):
            new_bit = (byte >> 7) & 1
            # print("nb", new_bit)
            msb = (res >> 6) & 1
            fb = msb ^ new_bit
            # print("fb", fb)
            res = res << 1
            # print("sr=",bin(res))
            if fb:
                res = res ^ 0x09
            # print("crc", res)

            byte = byte << 1

    return res & 0b01111111

assert crc7([0x40]) == 0x64
assert crc7([0x40, 0, 0, 0, 0]) == 0x4a

def reverse_bits(n: int, sz: int):
    result = 0
    for i in range(sz):
        result = (result << 1) | (n & 1)
        n >>= 1
    return result

def build_command(cmd: int, arg: int):
    """
    Build an SD command as a single 48-bit number
    :param cmd: The command id
    :param arg: The command argument
    :return: The full 48-bit command, with crc already computed
    """
    # start(1)=0 | direction bit(1)=1 | cmd(6) | arg(32) | crc(7) | end(1)=1
    cmd_no_crc = 0b0 \
     | (1 << 1) \
     | (reverse_bits(cmd, 6) << 2) \
     | (reverse_bits(arg, 32) << 8)

    crc = crc7(reverse_bits(cmd_no_crc, 40).to_bytes(5, byteorder="big"))

    return cmd_no_crc \
            | (reverse_bits(crc, 7) << 40) \
            | (1 << 47)

def build_cmd0():
    """
    Build the GO_IDLE_STATE command that fully resets all connected cards
    :return:
    """
    return build_command(cmd=0, arg=0)

def build_cmd8():
    """
    Build the SEND_IF_COND command that checks if the card supports the provided voltage
    """
    check = 0xAA
    vhs = 0b0001 # 2.7v-3.6v

    return build_command(cmd=8, arg=(vhs << 8) | check)

def build_cmd55(rca: int):
    """
    Builds the APP_CMD command that indicates the next command is an ACMD
    :param rca: The RCA of the target card, 0 for unselected cards
    """
    return build_command(cmd=55, arg=rca<<16)

def build_acmd41(hcs: bool, xpc: bool, voltage: int):
    """
    Builds the SD_SEND_OP_COND app command that either requests the OCR or checks if the card can support a
    given voltage range
    :return:
    """
    arg = 0
    if hcs:
        arg |= 1<<30
    if xpc:
        arg |= 1<<28
    arg |= voltage << 8
    return build_command(cmd=41, arg=arg)

def build_cmd2():
    """
    Builds the ALL_SEND_CID command that requests the CID of all connected cards
    """
    return build_command(cmd=2, arg=0)

def build_cmd3():
    """
    Builds the SEND_RELATIVE_ADDR command that requests the relative address (RCA) of the card
    """
    return build_command(cmd=3, arg=0)

def build_cmd7(rca: int):
    """
    Builds the SELECT_CARD command that switches a specific card to the transfer state
    """
    return build_command(cmd=7, arg=rca<<16)

def build_cmd9(rca: int):
    """
    Builds the SEND_CSD command that requests the CSD of the specified card
    """
    return build_command(cmd=9, arg=rca<<16)

def build_acmd51():
    """
    Builds the SEND_SCR command that requests the SCR of the card
    """
    return build_command(cmd=51, arg=0)

def build_cmd16():
    """
    Builds the SET_BLOCKLEN command that sets the block size of future reads
    """
    # Default to 512 bytes
    return build_command(cmd=16, arg=0x200)

def build_cmd17(addr: int):
    """
    Builds the READ_SINGLE_BLOCK command that reads a given block from the card
    :param addr: The block index to read
    """
    return build_command(cmd=17, arg=addr)

def build_cmd32(addr: int):
    """
    Builds the ERASE_WR_BLK_START command that sets the start block for an erase operation
    :param addr: The start block to erase
    """
    return build_command(cmd=32, arg=addr)

def build_cmd33(addr: int):
    """
    Builds the ERASE_WR_BLK_END command that sets the end block for an erase operation
    :param addr: The end block to erase
    """
    return build_command(cmd=33, arg=addr)

def build_cmd38(func: int):
    """
    Builds the ERASE command that performs an erase operation
    :param func: The erase function to perform
    """
    return build_command(cmd=38, arg=func)