from dataclasses import dataclass
from enum import Enum
from typing import Type


class InstrumentType(str, Enum):
    POWER_SUPPLY = "Power Supply"
    OSCILLOSCOPE = "Oscilloscope"
    ELECTRONIC_LOAD = "Electronic Load"
    UNKNOWN = "Unknown"


@dataclass
class ISpec:
    name: str
    address: str
    make: str
    model: str
    serial_number: str
    firmware_version: str
    instrument_type: InstrumentType
    instrument_class: Type | None
