from dataclasses import dataclass

from glasgow.applet.memory.mmc import BaseMsg
from glasgow.applet.memory.mmc.card_status import CardStatus


@dataclass
class R1Response:
    """
    The R1 response, contains the current status of the card
    """
    base: BaseMsg

    status: CardStatus

    def __init__(self, base: BaseMsg):
        self.base = base
        self.status = CardStatus(base.payload)