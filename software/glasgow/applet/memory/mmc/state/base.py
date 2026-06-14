from typing import Optional

from glasgow.applet.memory.mmc.base_msg import BaseMsg


class BaseState:
    """
    A base state class, used with the command state machine
    """
    def __init__(self):
        pass

    async def on_message(self, m: BaseMsg, iface) -> Optional[bool]:
        """
        Called every time a new message if received from the PHY
        :param m: The new message
        :param iface: The interface instance
        :return: True if we should progress to the next state
        """
        pass

    async def on_new_state(self, iface):
        """
        Called when this state is entered
        :param iface: The interface instance
        :return: None
        """
        pass
