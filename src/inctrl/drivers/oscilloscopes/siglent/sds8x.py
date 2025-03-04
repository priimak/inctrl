from inctrl import Duration, ScopeChanel
from inctrl.drivers.command_dispatcher import CommandDispatcher
from inctrl.model import TriggerNamespace, ISpec
from inctrl.model.oscilloscope import Oscilloscope, ScopeProperties
from inctrl.model.time import TimeUnit


class SDS8Oscilloscope(Oscilloscope):
    def __init__(self, spec: ISpec, cmd: CommandDispatcher):
        self._spec = spec
        self._cmd = cmd

    def channel(self, channel: int | str) -> ScopeChanel:
        pass

    @property
    def trigger(self) -> TriggerNamespace:
        pass

    def set_time_window(self, time_window: str | Duration) -> Duration:
        pass

    def get_time_window(self) -> Duration:
        pass

    def set_time_scale(self, scale: str | Duration) -> Duration:
        target_scale_s = Duration.value_of(scale).in_unit(TimeUnit.S)
        self._cmd.write(f":TIMEBASE:SCALE {target_scale_s}")
        return self.get_time_scale()

    def get_time_scale(self) -> Duration:
        res = self._cmd.query(":TIMEBASE:SCALE?")
        return Duration.value_of(f"{res} s")

    @property
    def properties(self) -> ScopeProperties:
        pass
