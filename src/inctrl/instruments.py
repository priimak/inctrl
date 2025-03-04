from typing import Any

from pyvisa import ResourceManager, Resource

from inctrl.drivers import INSTRUMENT_DB_INSTANCE
from inctrl.drivers.command_dispatcher import CommandDispatcher
from inctrl.model import ISpec, InstrumentType
from inctrl.model.oscilloscope import Oscilloscope


def list_instruments() -> list[ISpec]:
    rm = ResourceManager()
    addresses = rm.list_resources()
    instrument_specs: list[ISpec] = []

    for address in addresses:
        resource: Resource = rm.open_resource(address)
        try:
            idn = resource.query("*IDN?")
            instrument_specs.append(INSTRUMENT_DB_INSTANCE.get_spec(address, idn))
        finally:
            resource.close()
    return instrument_specs


def _get_spec(address: str) -> tuple[CommandDispatcher, ISpec]:
    rm = ResourceManager()
    resource = rm.open_resource(address)
    if resource is None:
        raise RuntimeError("Resource not found")
    else:
        idn = resource.query("*IDN?")
        return CommandDispatcher(resource), INSTRUMENT_DB_INSTANCE.get_spec(address, idn)


def oscilloscope(address: str, capabilities: dict[str, Any] | None = None) -> Oscilloscope:
    """
    Return oscilloscope for a given address. If `capabilities` is provided, then ensure that oscilloscope
    to be instantiated does have requested capabilities. Raises RuntimeError if instrument under this
    address is not available or is not an oscilloscope, or it does not have requested capabilities.
    Capabilities might be scope make, model, number of channels, sampling rate and so on.
    """
    cmd, spec = _get_spec(address)
    if spec.instrument_type == InstrumentType.OSCILLOSCOPE:
        return spec.instrument_class(spec, cmd)
    else:
        raise RuntimeError("This instrument is not an oscilloscope")
