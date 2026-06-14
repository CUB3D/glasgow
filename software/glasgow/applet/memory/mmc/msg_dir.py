from enum import Enum


class MsgDir(Enum):
    """
    The direction of a message in a SD command
    """
    # The message is from the card to the host
    Card = 0
    # The message is from the host to the card
    Host = 1