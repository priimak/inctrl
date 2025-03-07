from abc import ABC, abstractmethod
from dataclasses import dataclass
from enum import Enum, IntEnum
from typing import Self, Type

from inctrl.model.time import Duration
from inctrl.model.waveform import Waveform


class TriggerSource(ABC):
    @abstractmethod
    def internal_id(self) -> str:
        pass


class ChannelCoupling(str, Enum):
    AC = "AC"
    DC = "DC"
    GND = "GND"


class ChannelImpedance(IntEnum):
    FIFTY_OHM = 50
    ONE_MOHM = 1_000_000


class ScopeChanel(TriggerSource):
    @abstractmethod
    def _scope(self) -> "Oscilloscope":
        pass

    @abstractmethod
    def get_waveform(self, name: str | None = None) -> Waveform:
        """ 
        Download waveform from the oscilloscope. Waveform will have a name derived from channel number 
        or if argument `name` is provided, it will be used as a Waveform name. 
        """

    ################################ Coupling ################################
    @abstractmethod
    def set_coupling(self, coupling: ChannelCoupling, fail_on_error: bool = False) -> ChannelCoupling:
        """
        Set coupling on the channel. If `fail_on_error` is set to True and requested coupling
        cannot be set (perhaps because it is unsupported), then RuntimeError will be raised.
        If `fail_on_error` is False (default), then simply return actually set channel coupling
        even if it is different from the requested.
        """

    @abstractmethod
    def get_coupling(self) -> ChannelCoupling:
        """ Get currently configured coupling on the channel. """

    ################################ Input Impedance ################################
    @abstractmethod
    def set_impedance_oHm(self, impedance_oHm: float, fail_on_error: bool = False) -> float:
        """
        Set impedance on the channel in OHm. If `fail_on_error` is set to True and requested impedance
        cannot be set (perhaps because it is an unsupported value), then RuntimeError will be raised.
        If `fail_on_error` is False (default), then simply return actually set impedance even if it is
        different from the requested.

        Allowed impedance values are usually a small discrete set, but can vary from one scope make
        and model to another. To obtain list of allowed impedance values for this scope
        call `scope.properties.get_impedance_list()`.
        """

    @abstractmethod
    def get_impedance_oHm(self) -> float:
        """ Return impedance configured on the channel. """

    def set_impedance_min(self) -> float:
        """ Set impedance to the minimum value and return actually configured value in oHm """
        return self.set_impedance_oHm(min(self._scope().properties.valid_impedance_values))

    def set_impedance_max(self) -> float:
        """ Set impedance to the maximum value and return actually configured value in oHm """
        return self.set_impedance_oHm(max(self._scope().properties.valid_impedance_values))

    ################################ Vertical Scaling ################################
    def set_range_V(self, v_min: float, v_max: float) -> tuple[float, float]:
        """
        Set voltage range to be at minimum from v_min to v_max and return actually configured range.
        Raises RuntimeError if v_min >= v_max.
        """
        scale = (v_max - v_min) / self._scope().properties.number_of_vertical_divisions
        self.set_scale_V(scale)
        self.set_offset_V((v_max - v_min) / 2 - v_max)
        return self.get_range_V()

    def get_range_V(self) -> tuple[float, float]:
        """ Return voltage range currently configured on the channel. """
        offset_V = self.get_offset_V()
        dv = self.get_scale_V() * self._scope().properties.number_of_vertical_divisions / 2
        return -offset_V - dv, -offset_V + dv

    @abstractmethod
    def set_scale_V(self, v: float) -> float:
        """ Set vertical scale in voltage per division and return actually set value. """

    @abstractmethod
    def get_scale_V(self) -> float:
        """ Return configured vertical scale in voltage per division. """

    @abstractmethod
    def set_offset_V(self, offset_V: float) -> float:
        """ Set vertical offset in volts and return actually set value. """

    @abstractmethod
    def get_offset_V(self) -> float:
        """ Return configured vertical offset in volts. """


class TriggerSlope(str, Enum):
    RISING = "RISING"
    FALLING = "FALLING"


class ScopeTrigger(ABC):
    def __init__(self, trigger_source: TriggerSource, delay: Duration):
        self.trigger_source = trigger_source
        self.delay = delay

    @classmethod
    def EDGE(cls,
             trigger_source: TriggerSource,
             level_V: float,
             slope: TriggerSlope = TriggerSlope.RISING,
             delay: str | Duration = Duration.value_of("0 s")) -> Self:
        return ScopeEdgeTrigger(trigger_source, level_V, slope, delay)


class ScopeEdgeTrigger(ScopeTrigger):
    def __init__(self,
                 trigger_source: TriggerSource,
                 level_V: float,
                 slope: TriggerSlope = TriggerSlope.RISING,
                 delay: str = "0 s"):
        super().__init__(trigger_source, Duration.value_of(delay))
        self.level_V = level_V
        self.slope = slope


class TriggerNamespace(ABC):
    @abstractmethod
    def configure(self, trigger: ScopeTrigger) -> None:
        """
        Apply trigger configuration. This might be irrelevant if trigger is fired manually or set to auto.
        """

    @abstractmethod
    def arm_single(self) -> None:
        """
        Arm trigger for a one shot accusation. This is a non-blocking function. To confirm that trigger
        is set call function `scope.trigger.is_armed()`. Note that conditions for trigger to be fired and therefore
        disarmed might be met even before this functions returns. In which case `is_armed()` called right after would
        return False.
        """

    @abstractmethod
    def arm_auto(self) -> None:
        """
        Arm trigger for periodic automatic firing. If this function is called trigger configuration is ignored.
        """

    @abstractmethod
    def arm_normal(self) -> None:
        """
        Arm trigger to be fired every time conditions as defined when `scope.trigger.configure(...)` was called.
        """

    @abstractmethod
    def wait_for_waveform(self, timeout: str | Duration | None = None, error_on_timeout: bool = False) -> bool:
        """
        Blocking call to wait for trigger to become activated and waveform available for downloading and return True.
        If above conditions were not met, then return False, unless error_on_timeout is True and timeout
        value is not None in which case RuntimeError will be raised.
        """

    @abstractmethod
    def is_armed(self) -> bool:
        """
        :return: True or False indicating if trigger is armed.
        """

    @abstractmethod
    def disarm(self) -> None:
        """
        Disarm this trigger. If trigger is explicitly disarmed,
        then calling wait_for_waveform(...) raises IllegalStateException.
        """


@dataclass(frozen = True)
class ScopeProperties:
    valid_impedance_values: list[float]
    number_of_time_divisions: int
    number_of_vertical_divisions: int
    number_of_channels: int


class Oscilloscope(ABC):
    def as_class[T: Oscilloscope](self, clazz: Type[T]) -> T:
        """ Cast instance of this class to `clazz` or raise RuntimeError it is not possible. """
        if isinstance(self, clazz):
            return self
        else:
            raise RuntimeError(f"Not an instance of {clazz.__name__}")

    @abstractmethod
    def channel(self, channel: int | str) -> ScopeChanel:
        """
        Return oscilloscope chanel for a given channel. Raises RuntimeError if channel isn't. preset.
        Channel symbolic name can can be configured in the instruments.json file.

        :param channel: channel number or name
        """

    @property
    @abstractmethod
    def trigger(self) -> TriggerNamespace:
        """ Access trigger namespace. """

    def set_time_window(self, time_window: str | Duration) -> Duration:
        """
        Ensure that capture time window will be at least as large as requested `time_window` value.
        Return actually set time window, which will always be equal or larger than requested value.
        """
        requested_time_window: Duration = Duration.value_of(time_window)
        requested_scale_ref: Duration = requested_time_window / self.properties.number_of_time_divisions
        requested_scale = requested_scale_ref
        for i in range(50):  # try max 50 times
            set_scale = self.set_time_scale(requested_scale)
            if set_scale >= requested_scale:
                return self.get_time_window()
            else:
                requested_scale = requested_scale_ref * (1 + 0.1 * i)
        return self.get_time_window()

    def get_time_window(self) -> Duration:
        """ Return current time window configured on the oscilloscope. """
        return (self.get_time_scale() * self.properties.number_of_time_divisions).optimize()

    @abstractmethod
    def set_time_scale(self, scale: str | Duration) -> Duration:
        """ Set timescale in duration per horizontal division and return actually set value. """

    @abstractmethod
    def get_time_scale(self) -> Duration:
        """ Return configured timescale in duration per horizontal division. """

    @property
    @abstractmethod
    def properties(self) -> ScopeProperties:
        """ Access oscilloscope properties. """

    @abstractmethod
    def reset(self) -> None:
        pass
