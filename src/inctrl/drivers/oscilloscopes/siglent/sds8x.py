import time
from struct import unpack

import numpy as np

from inctrl import Duration, ScopeChanel, ChannelCoupling, ScopeTrigger
from inctrl.drivers.command_dispatcher import CommandDispatcher
from inctrl.model import TriggerNamespace, ISpec, Waveform
from inctrl.model.oscilloscope import Oscilloscope, ScopeProperties, ScopeEdgeTrigger, TriggerSlope
from inctrl.model.time import TimeUnit


class SDS8OscilloscopeChannel(ScopeChanel):
    def __init__(self, scope, channel_num: int):
        self.scope: SDS8Oscilloscope = scope
        self.__channel_num = channel_num

    def _scope(self) -> "Oscilloscope":
        return self.scope

    def internal_id(self) -> str:
        return f"C{self.__channel_num}"

    def get_waveform(self) -> Waveform:
        tdiv_enum = [200e-12, 500e-12, 1e-9, 2e-9, 5e-9, 10e-9, 20e-9, 50e-9, 100e-9, 200e-9, 500e-9, 1e-6, 2e-6, 5e-6,
                     10e-6, 20e-6, 50e-6, 100e-6, 200e-6, 500e-6, 1e-3, 2e-3, 5e-3, 10e-3, 20e-3, 50e-3, 100e-3, 200e-3,
                     500e-3, 1, 2, 5, 10, 20, 50, 100, 200, 500, 1000]
        max_point = int(self.scope._cmd.query(":WAVEFORM:MAXPOINT?"))
        self.scope._cmd.write(":WAVEFORM:BYTEORDER LSB")
        self.scope._cmd.write(":WAVEFORM:START 0")
        self.scope._cmd.write(f":WAVEFORM:POINT {max_point}")
        self.scope._cmd.write(":WAVEFORM:INTERVAL 1")
        self.scope._cmd.write(":WAVEFORM:WIDTH WORD")
        self.scope._cmd.write(f":WAVEFORM:SOURCE C{self.__channel_num}")

        header = self.scope._cmd.query_bytes(":WAVEFORM:PREAMBLE?")
        num_points = unpack("<L", header[116:120])[0]
        vertical_scale = unpack("<f", header[156:160])[0]  # "vdiv"
        vertical_offset = unpack("<f", header[160:164])[0]  # "offset"
        code_per_division = unpack("<f", header[164:168])[0]  # "code"
        horizontal_interval = unpack("<f", header[176:180])[0]  # "interval"
        trigger_offset_s = unpack("<d", header[180:188])[0]  # "delay"
        time_base = tdiv_enum[unpack("<H", header[324:326])[0]]  # "tdiv"

        data = self.scope._cmd.query_bytes(":WAVEFORM:DATA?")
        ys = [v * vertical_scale / code_per_division - vertical_offset for v in list(np.frombuffer(data, "<h"))]
        return Waveform(
            dx_s = horizontal_interval,
            trigger_index = int(
                (
                        time_base * self.scope.properties.number_of_time_divisions / 2 - trigger_offset_s
                ) / horizontal_interval
            ),
            ys = np.array(ys)
        )

    def set_coupling(self, coupling: ChannelCoupling, fail_on_error: bool = False) -> ChannelCoupling:
        self.scope._cmd.write(f":CHANNEL{self.__channel_num}:COUPLING {coupling.value}", synchronize = True)
        configured_coupling: ChannelCoupling = self.get_coupling()
        if configured_coupling != coupling and fail_on_error:
            raise RuntimeError(f"Failed to set coupling to \"{coupling.value}\"")
        else:
            return configured_coupling

    def get_coupling(self) -> ChannelCoupling:
        coupling = self.scope._cmd.query(f":CHANNEL{self.__channel_num}:COUPLING?")
        match coupling:
            case "AC":
                return ChannelCoupling.AC
            case "DC":
                return ChannelCoupling.DC
            case "GND":
                return ChannelCoupling.DC
            case _:
                raise RuntimeError(f"Unknown coupling \"{coupling}\".")

    def set_scale_V(self, v: float) -> float:
        self.scope._cmd.write(f":CHANNEL{self.__channel_num}:SCALE {v}", synchronize = True)
        return self.get_scale_V()

    def get_scale_V(self) -> float:
        return float(self.scope._cmd.query(f":CHANNEL{self.__channel_num}:SCALE?"))

    def set_offset_V(self, offset_V: float) -> float:
        self.scope._cmd.write(f":CHANNEL{self.__channel_num}:OFFSET {offset_V}", synchronize = True)
        return self.get_offset_V()

    def get_offset_V(self) -> float:
        return float(self.scope._cmd.query(f":CHANNEL{self.__channel_num}:OFFSET?"))

    def set_impedance_oHm(self, impedance_oHm: float, fail_on_error: bool = False) -> float:
        if impedance_oHm == 50.0:
            self.scope._cmd.write(f":CHANNEL{self.__channel_num}:IMPEDANCE FIFTy", synchronize = True)
        elif impedance_oHm == 1_000_000.0:
            self.scope._cmd.write(f":CHANNEL{self.__channel_num}:IMPEDANCE ONEMeg", synchronize = True)
        elif fail_on_error:
            raise RuntimeError(f"Failed to set impedance to \"{impedance_oHm}\" OHm")

        configured_impedance_oHm = self.get_impedance_oHm()
        if configured_impedance_oHm != impedance_oHm and fail_on_error:
            raise RuntimeError(f"Failed to set impedance to \"{impedance_oHm}\" OHm")

        return configured_impedance_oHm

    def get_impedance_oHm(self) -> float:
        impedance = self.scope._cmd.query(f":CHANNEL{self.__channel_num}:IMPEDANCE?").lower()
        match impedance:
            case "onemeg":
                return 1_000_000.0
            case "fifty":
                return 50.0
            case _:
                raise RuntimeError(f"Unknown impedance \"{impedance}\".")


class SDS8OscilloscopeTriggerNamespace(TriggerNamespace):
    def __init__(self, scope):
        self.scope: SDS8Oscilloscope = scope

    def configure(self, trigger: ScopeTrigger) -> None:
        if isinstance(trigger, ScopeEdgeTrigger):
            self.scope._cmd.write(":TRIGGER:TYPE EDGE")
            self.scope._cmd.write(f":TRIGGER:EDGE:SOURCE {trigger.trigger_source.internal_id()}")
            self.scope._cmd.write(f":TRIGGER:EDGE:LEVEL {trigger.level_V}")

            match trigger.slope:
                case TriggerSlope.RISING:
                    self.scope._cmd.write(f":TRIGGER:EDGE:SLOPE RISING")
                case TriggerSlope.FALLING:
                    self.scope._cmd.write(f":TRIGGER:EDGE:SLOPE FALLING")
                case _:
                    raise RuntimeError(f"Unknown trigger slope \"{trigger.slope}\".")

            target_scale_s = trigger.delay.in_unit(TimeUnit.S)
            self.scope._cmd.write(f":TIMEBASE:DELAY {target_scale_s}", synchronize = True)
        else:
            raise RuntimeError(f"Unknown scope trigger \"{trigger}\".")

    def arm_single(self) -> None:
        self.scope._cmd.write(":TRIGGER:MODE SINGLE")
        self.scope._cmd.write(":TRIGGER:RUN", synchronize = True)

    def arm_auto(self) -> None:
        self.scope._cmd.write(":TRIGGER:MODE AUTO")
        self.scope._cmd.write(":TRIGGER:RUN", synchronize = True)

    def arm_normal(self) -> None:
        self.scope._cmd.write(":TRIGGER:MODE NORMAL")
        self.scope._cmd.write(":TRIGGER:RUN", synchronize = True)

    def wait_for_waveform(self, timeout: str | Duration | None = None, error_on_timeout: bool = False) -> bool:
        timeout_s = -1 if timeout is None else Duration.value_of(timeout).to_float(TimeUnit.S)
        mode = self.scope._cmd.query(f":TRIGGER:MODE?").lower()
        start_at = time.time()
        if mode == "single":
            while True:
                trig_status = self.scope._cmd.query(f":TRIGGER:STATUS?").lower()
                if trig_status == "stop":
                    return True
                elif timeout_s >= 0:
                    if time.time() - start_at >= timeout_s:
                        if error_on_timeout:
                            raise RuntimeError(f"Timeout {timeout} exceeded.")
                        else:
                            return False
        else:
            while True:
                inr = int(self.scope._cmd.query("INR?").lower().replace("inr", "").strip())
                if inr & 0x01 == 1:
                    return True
                elif timeout_s >= 0:
                    if time.time() - start_at >= timeout_s:
                        if error_on_timeout:
                            raise RuntimeError(f"Timeout {timeout} exceeded.")
                        else:
                            return False

    def is_armed(self) -> bool:
        return self.scope._cmd.query(":TRIGGER:STATUS?").lower() != "stop"

    def disarm(self) -> None:
        self.scope._cmd.write(":TRIGGER:STOP", synchronize = True)


class SDS8Oscilloscope(Oscilloscope):
    def __init__(self, spec: ISpec, cmd: CommandDispatcher):
        self._spec = spec
        self._cmd = cmd

        self.__properties = ScopeProperties(
            valid_impedance_values = [1000000.0],
            number_of_time_divisions = 10,
            number_of_vertical_divisions = 8,
            number_of_channels = int(spec.model[5]),
        )

        self.__trigger_namespace = SDS8OscilloscopeTriggerNamespace(self)

    def channel(self, channel: int | str) -> SDS8OscilloscopeChannel:
        self._cmd.write(f":CHANNEL{channel}:SWITCH ON")
        self._cmd.write(f":CHANNEL{channel}:VISIBLE ON")
        return SDS8OscilloscopeChannel(self, channel)

    @property
    def trigger(self) -> SDS8OscilloscopeTriggerNamespace:
        return self.__trigger_namespace

    def set_time_scale(self, scale: str | Duration) -> Duration:
        target_scale_s = Duration.value_of(scale).in_unit(TimeUnit.S)
        self._cmd.write(f":TIMEBASE:SCALE {target_scale_s}", synchronize = True)
        return self.get_time_scale()

    def get_time_scale(self) -> Duration:
        res = self._cmd.query(":TIMEBASE:SCALE?")
        return Duration.value_of(f"{res} s").optimize()

    @property
    def properties(self) -> ScopeProperties:
        return self.__properties

    def reset(self) -> None:
        self._cmd.write("*RST", synchronize = True)

        for channel in range(1, self.properties.number_of_channels + 1):
            self._cmd.write(f":CHANNEL{channel}:SWITCH OFF")
            self._cmd.write(f":CHANNEL{channel}:VISIBLE OFF", synchronize = True)
