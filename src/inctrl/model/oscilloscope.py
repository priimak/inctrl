from abc import ABC, abstractmethod
from enum import Enum
from typing import Self

from inctrl.model.time import Duration
from inctrl.model.waveform import Waveform


class TriggerSource(ABC):
    pass


class ChannelCoupling(str, Enum):
    AC = "AC"
    DC = "DC"
    GND = "GND"


class ScopeChanel(TriggerSource):
    @abstractmethod
    def get_waveform(self) -> Waveform:
        pass

    @abstractmethod
    def set_coupling(self, coupling: ChannelCoupling) -> None:
        """ Set coupling on the channel. """

    @abstractmethod
    def get_coupling(self) -> ChannelCoupling:
        """ Get currently configured coupling on the channel. """

    def set_range(self, v_min: float, v_max: float) -> tuple[float, float]:
        """
        Set voltage range to be at minimum from v_min to v_max and return actually configured range.
        Raises RuntimeError if v_min >= v_max.
        """

    def get_range(self) -> tuple[float, float]:
        """
        Return voltage range currently configured on the channel.
        """


class TriggerSlope(str, Enum):
    NEGATIVE = "NEGATIVE"
    POSITIVE = "POSITIVE"


class ScopeTrigger(ABC):
    def __init__(self, trigger_source: TriggerSource, delay: Duration):
        self.trigger_source = trigger_source
        self.delay = delay

    @classmethod
    def EDGE(cls,
             trigger_source: TriggerSource,
             level_V: float,
             slope: TriggerSlope = TriggerSlope.POSITIVE,
             delay: str = "0 s") -> Self:
        return ScopeEdgeTrigger(trigger_source, level_V, slope, delay)


class ScopeEdgeTrigger(ScopeTrigger):
    def __init__(self,
                 trigger_source: TriggerSource,
                 level_V: float,
                 slope: TriggerSlope = TriggerSlope.POSITIVE,
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
    def wait_for_waveform(self, timeout: str | None = None, error_on_timeout: bool = False) -> bool:
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


class Oscilloscope(ABC):
    @abstractmethod
    def channel(self, channel: int | str) -> ScopeChanel:
        """
        Return oscilloscope chanel for a given channel. Raises RuntimeError if channel isn't. preset.
        Channel symbolic name can can be configured in the instruments.json file.

        :param channel: channel number or name
        """

    @abstractmethod
    @property
    def trigger(self) -> TriggerNamespace:
        pass

    @abstractmethod
    def set_time_window(self, time_window: str | Duration) -> Duration:
        """
        Ensure that capture time window will be at least as large as requested `time_window` value.
        Return actually set time window, which will always equal or larger than requested .
        """

    @abstractmethod
    def get_time_window(self) -> Duration:
        """ Return current time window configured on the oscilloscope. """
