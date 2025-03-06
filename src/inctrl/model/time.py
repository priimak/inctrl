import re
from enum import IntEnum
from typing import Self


class TimeUnit(IntEnum):
    NS = 1
    US = 1_000
    MS = 1_000_000
    S = 1_000_000_000
    KS = 1_000_000_000_000

    @staticmethod
    def value_of(s: str | Self) -> "TimeUnit":
        if isinstance(s, str):
            match s:
                case "ns":
                    return TimeUnit.NS
                case "us":
                    return TimeUnit.US
                case "ms":
                    return TimeUnit.MS
                case "s":
                    return TimeUnit.S
                case "ks":
                    return TimeUnit.KS
                case _:
                    raise RuntimeError(f"Unknown time unit: {s}")
        else:
            return s

    def to_str(self) -> str:
        match self:
            case TimeUnit.NS:
                return "ns"
            case TimeUnit.US:
                return "us"
            case TimeUnit.MS:
                return "ms"
            case TimeUnit.S:
                return "s"
            case TimeUnit.KS:
                return "ks"
            case _:
                raise RuntimeError(f"Unknown time unit: {self}")


class Duration:
    __matcher = re.compile(r"""^(?P<value>-?\d+(?:\.\d+)?(?:[eE][+-]?\d+)?)\s*(?P<unit>ks|s|ms|us|ns)$""")

    def __init__(self, time_interval: float, time_unit: TimeUnit):
        self.__time_interval = time_interval
        self.time_unit = time_unit

    def __str__(self):
        return f"{self.__time_interval} {self.time_unit.to_str()}"

    def __mul__(self, scale):
        return Duration(self.__time_interval * scale, self.time_unit)

    def __rmul__(self, scale):
        return Duration(self.__time_interval * scale, self.time_unit)

    def __truediv__(self, scale):
        return Duration(self.__time_interval / scale, self.time_unit)

    def __gt__(self, other):
        return self.__time_interval > other.to_float(self.time_unit)

    def __ge__(self, other):
        return self.__time_interval >= other.to_float(self.time_unit)

    def __lt__(self, other):
        return self.__time_interval < other.to_float(self.time_unit)

    def __le__(self, other):
        return self.__time_interval <= other.to_float(self.time_unit)

    def __eq__(self, other):
        return self.__time_interval == other.to_float(self.time_unit)

    def in_unit(self, time_unit: str | TimeUnit) -> Self:
        target_time_unit = TimeUnit.value_of(time_unit)
        return Duration(
            self.__time_interval * self.time_unit.value / target_time_unit.value,
            target_time_unit
        )

    @staticmethod
    def value_of(s: str | Self) -> "Duration":
        if isinstance(s, Duration):
            return s
        match_result = Duration.__matcher.match(s)
        if match_result:
            return Duration(float(match_result.group('value')), TimeUnit.value_of(match_result.group('unit')))

    def to_float(self, time_unit: str | TimeUnit) -> float:
        return self.__time_interval * self.time_unit.value / TimeUnit.value_of(time_unit).value

    def optimize(self) -> Self:
        for time_unit in [TimeUnit.KS, TimeUnit.S, TimeUnit.MS, TimeUnit.US, TimeUnit.NS]:
            if 1000 > self.to_float(time_unit) >= 1:
                return self.in_unit(time_unit)

        return self.in_unit(TimeUnit.NS)
