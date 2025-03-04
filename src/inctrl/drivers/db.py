import re

from inctrl.model import ISpec, InstrumentType

IDN_REGEX = re.compile("^(?P<make>.+),(?P<model>.+),(?P<serial_number>.+),(?P<firmware>.+)$")


def _idn_to_spec_initial(address: str, idn: str) -> ISpec:
    idn_match = IDN_REGEX.match(idn)
    if idn_match:
        return ISpec(
            name = address,
            address = address,
            make = idn_match.group("make"),
            model = idn_match.group("model"),
            serial_number = idn_match.group("serial_number"),
            firmware_version = idn_match.group("firmware"),
            instrument_type = InstrumentType.UNKNOWN,
            instrument_class = None
        )
    else:
        return ISpec(
            name = address,
            address = address,
            make = "",
            model = "",
            serial_number = "",
            firmware_version = "",
            instrument_type = InstrumentType.UNKNOWN,
            instrument_class = None
        )


class InstrumentsDB:
    def __resolve_siglent(self, spec: ISpec) -> ISpec:
        if spec.model.startswith("SDS8"):
            # SDS8*** oscilloscope
            spec.instrument_type = InstrumentType.OSCILLOSCOPE
            from inctrl.drivers.oscilloscopes.siglent.sds8x import SDS8Oscilloscope
            spec.instrument_class = SDS8Oscilloscope
        return spec

    def get_spec(self, address: str, idn: str) -> ISpec:
        spec: ISpec = _idn_to_spec_initial(address, idn)
        match spec.make:
            case "Siglent Technologies":
                return self.__resolve_siglent(spec)
            case _:
                return spec


INSTRUMENT_DB_INSTANCE = InstrumentsDB()
