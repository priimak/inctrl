import re
from enum import IntEnum
from typing import Self, Any


class TimeUnit(IntEnum):
    NS = 1
    US = 1_000
    MS = 1_000_000
    S = 1_000_000_000
    KS = 1_000_000_000_000

    @staticmethod
    def value_of(s: Any) -> "TimeUnit":
        if isinstance(s, TimeUnit):
            return s
        else:
            match f"{s}".lower():
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
    __matcher = re.compile(
        r"""^\s*(?P<value>-?\d+(?:\.\d+)?(?:[eE][+-]?\d+)?)\s*(?P<unit>ks|s|ms|us|ns|KS|S|MS|US|NS)\s*$"""
    )

    def __init__(self, time_interval: float, time_unit: TimeUnit):
        self.__time_interval = time_interval
        self.time_unit = time_unit

    def __str__(self):
        return f"{self.__time_interval} {self.time_unit.to_str()}"

    def __repr__(self):
        return f"Duration({self.__time_interval}, {self.time_unit.to_str()})"

    def __add__(self, other):
        if isinstance(other, Duration):
            return Duration(
                time_interval = self.__time_interval + other.to_float(self.time_unit),
                time_unit = self.time_unit
            ).optimize()

    def __sub__(self, other):
        if isinstance(other, Duration):
            return Duration(
                time_interval = self.__time_interval - other.to_float(self.time_unit),
                time_unit = self.time_unit
            ).optimize()

    def __mul__(self, scale):
        return Duration(self.__time_interval * scale, self.time_unit)

    def __rmul__(self, scale):
        return Duration(self.__time_interval * scale, self.time_unit)

    def __truediv__(self, scale):
        return Duration(self.__time_interval / scale, self.time_unit)

    def __gt__(self, other):
        if isinstance(other, Duration):
            return self.__time_interval > other.to_float(self.time_unit)
        else:
            raise RuntimeError("Duration can only be compared to another duration")

    def __ge__(self, other):
        if isinstance(other, Duration):
            return self.__time_interval > other.to_float(self.time_unit) or self == other
        else:
            raise RuntimeError("Duration can only be compared to another duration")

    def __lt__(self, other):
        if isinstance(other, Duration):
            return self.__time_interval < other.to_float(self.time_unit)
        else:
            raise RuntimeError("Duration can only be compared to another duration")

    def __le__(self, other):
        if isinstance(other, Duration):
            return self.__time_interval < other.to_float(self.time_unit) or self == other
        else:
            raise RuntimeError("Duration can only be compared to another duration")

    def __eq__(self, other):
        if isinstance(other, Duration):
            return abs(self - other) < ONE_PICOSECOND
        else:
            raise RuntimeError("Duration can only be compared to another duration")

    def __abs__(self):
        return Duration(abs(self.__time_interval), self.time_unit)

    def in_unit(self, time_unit: str | TimeUnit) -> Self:
        target_time_unit = TimeUnit.value_of(time_unit)
        return Duration(
            self.__time_interval * self.time_unit.value / target_time_unit.value,
            target_time_unit
        )

    @staticmethod
    def value_of(s: Any) -> "Duration":
        if isinstance(s, Duration):
            return s
        match_result = Duration.__matcher.match(f"{s}")
        if match_result:
            return Duration(float(match_result.group('value')), TimeUnit.value_of(match_result.group('unit')))
        else:
            raise RuntimeError(f"Unable to parse \"{s}\" as duration")

    def to_float(self, time_unit: str | TimeUnit) -> float:
        return self.__time_interval * self.time_unit.value / TimeUnit.value_of(time_unit).value

    def optimize(self) -> Self:
        for time_unit in [TimeUnit.KS, TimeUnit.S, TimeUnit.MS, TimeUnit.US, TimeUnit.NS]:
            if 1000 > self.to_float(time_unit) >= 1:
                return self.in_unit(time_unit)

        return self.in_unit(TimeUnit.NS)


ONE_PICOSECOND = Duration.value_of("0.001ns")
