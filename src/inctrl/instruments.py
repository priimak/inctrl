from typing import Any

from inctrl.model.oscilloscope import Oscilloscope


class X(Oscilloscope):
    pass


def oscilloscope(address: str, capabilities: dict[str, Any] | None = None) -> Oscilloscope:
    """
    Return oscilloscope for a given address. If `capabilities` is provided, then ensure that oscilloscope
    to be instantiated does have requested capabilities. Raises RuntimeError if instrument under this
    address is not available or is not an oscilloscope, or it does not have requested capabilities.
    Capabilities might be scope make, model, number of channels, sampling rate and so on.
    """
    return Oscilloscope()
