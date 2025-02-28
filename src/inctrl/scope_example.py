from inctrl.model import Oscilloscope, ScopeChanel, ChannelCoupling, ScopeTrigger

if __name__ == '__main__':
    scope = Oscilloscope()
    scope.set_time_window("22 us")

    c1: ScopeChanel = scope.channel(1)
    c1.set_coupling(ChannelCoupling.AC)
    c1.set_range(-1, 10)

    scope.trigger.arm_single(ScopeTrigger.EDGE(c1, level_V = 0.5))
    scope.trigger.wait_for_waveform(timeout = "5 s", error_on_timeout = True)
    scope.trigger.is_armed()
    scope.trigger.disarm()

    c1_waveform = c1.get_waveform()

    print(c1_waveform)
