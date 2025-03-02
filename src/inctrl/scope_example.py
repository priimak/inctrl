from inctrl import ScopeTrigger, oscilloscope, TriggerSlope

# Obtain handle to the connected oscilloscope
scope = oscilloscope("$address")

# We want to capture a 20 us waveform, hence we set time window 
# to a bit larger value
scope.set_time_window("23 us")

# Channel 1 refers to SCL (system clock) line
scl = scope.channel(1)
scl.set_impedance_max()

# Channel 1 refers to SDC (data) line
sdc = scope.channel(2)
sdc.set_impedance_max()

# Signals will be from 0 to 3.3 V. Setting range from -0.2 to 4 volts
# will ensure that all data is captured including noise.
scl.set_range_V(-0.2, 4)
sdc.set_range_V(-0.2, 4)

scope.trigger.configure(ScopeTrigger.EDGE(
    # trigger on voltage change in data line
    trigger_source = sdc,

    # trigger when voltage crosses 1.6 volt on the way down
    # to 0 from 3.3 volts
    level_V = 1.6,

    # we are interested in mosty what happens after the trigger point
    delay = "-20 us",

    # capture on the falling edge as by default signal is pulled up
    slope = TriggerSlope.FALLING
))

# arm trigger, download waveforms and save them to files.
scope.trigger.arm_single()
scope.trigger.wait_for_waveform("10 s", error_on_timeout = True)
csl_waveform = scl.get_waveform()
sdc_waveform = sdc.get_waveform()
csl_waveform.save_to_file("csl.wfm")
sdc_waveform.save_to_file("sdc.wfm")
