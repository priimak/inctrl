from inctrl.model.capabilities import Capabilities
from inctrl.model.oscilloscope import Oscilloscope


def oscilloscope(address: str, capabilities: Capabilities | None = None) -> Oscilloscope:
    """
    Return oscilloscope for a given address. If `capabilities` is provided, then ensure that oscilloscope 
    to be instantiated does have requested capabilities. Raises RuntimeError if instrument under this 
    address is not available or is not an oscilloscope or it does not have requested capabilities.
    """
    return Oscilloscope()
