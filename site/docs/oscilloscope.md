Oscilloscope
============

## Instantiation

Oscilloscope class is instantiated like so

```python
from inctrl import oscilloscope, Oscilloscope

scope: Oscilloscope = oscilloscope("$address")
```

Address argument allows to access a particular oscilloscope connected to your computer or present on the network.
This address string could be a [VISA](https://en.wikipedia.org/wiki/Virtual_instrument_software_architecture) address
or an alias. In the case of alias actual address (and some other parameters) has to be resolved by some means. Details
of that are in the "[Instrument name and parameters resolution](./name_resolution.md)" page.

Returned object (assigned to the variable `scope`) is an instance of `Oscilloscope` class. Which instance, will
depend on identification of the scope or can be forced though name and parameter resolution.

To ensure that oscilloscope to which you are connecting has required properties you can also pass `capability` argument.
For example, let say you require scope to have 8 channels. You can do it like so:

```python
scope: Oscilloscope = oscilloscope(
    "$address", capabilities = {"num_channels": 8}
)
```

Another way to ensure that you got instrument and a class that you want is to call `scope.as_class(...)` method. For
example if you want to ensure that you are working with LeCroy scope you do following.

```python
from inctrl.drivers.oscilloscope import LeCroyOscilloscope

scope: LeCroyOscilloscope = oscilloscope("$address").as_class(LeCroyOscilloscope)
```

If oscilloscope that you are connecting here is not a LeCroy scope then calling `as_class(LeCroyOscilloscope)` will
raise RuntimeError. This way you can ensure you connect to a specific make of the oscilloscope and obtain access to
methods unique to that particual scope.

## Capabilities

TBD

## Interacting with the scope

An oscilloscope has several logical components, primary being (1) the scope itself as
a whole, (2) channels and (3) a trigger.

### Scope as a whole

At this level you can set time window for scope capture like so:

```python
from inctrl.model import Duration

time_window: Duration = scope.set_time_window("22 us")
```

Argument to this function is a string containing time interval in the human-readable form or an instance of
class `Duration`. Since often not every time interval can be set, this function returns actually set duration
for the capture window. However, we guarantee that actually set time window will always be greater or equal
to the requested value and never less.

Alternatively you can set duration per time division, also known as _time scale_

```python
from inctrl.model import Duration

time_per_div: Duration = scope.set_time_scale("5 us")
```

Similarly to `set_time_window(...)` function `set_time_scale(...)` also returns actually set value.

Configured values can also be retrieved by calling `scope.get_time_window()` and `scope.get_time_scale()`.

### Channel

To obtain handles to a given scope channel you can call `scope.channel(...)` function. This function accepts
either channel number of channel name. In the later case channel name has to be defined through mechanisms
described in "[Instrument name and parameters resolution](./name_resolution.md)" page.

```python
ch3 = scope.channel(3)
clk = scope.channel("CLK")
```

Using these variables you can now interact with this channel and adjust various properties associated it.

#### Coupling

Channel coupling can by set by calling `set_coupling(coupling: ChannelCoupling, fail_on_error: bool = False)` method.

```python
from inctrl import ChannelCoupling

ch3.set_coupling(ChannelCoupling.AC)
```

Not every kind of coupling might be supported on the scope. Possible coupling constants are AC, DC and GND.
If `fail_on_error` argument is set to False (default), then simply return configured coupling even if unable
to set requested coupling type. If If `fail_on_error` is True and fail to set requested coupling, then
raise `RuntimeError`.

Use companion function `channel.get_coupling()` to obtain currently configured coupling on the channel.

#### Vertical scaling and offset

To ensure that signal you are trying to capture does not clip you can call function `set_range(...)`. This function
is provided as an alternative to setting voltage per division and offset.

```python
ch3_Vmin, ch3_Vmax = ch3.set_range_V(-1, 10)
```

This function guaranteed to set voltage per division and vertical offset such that requested voltage range fits
on the screen. It returns a tuple of actually set min and max values. These will usually match with voltage range
and scope screen. Voltage range as configured on the scope can always be retrieved by calling `get_range_V()`.

```python
ch3_Vmin, ch3_Vmax = ch3.get_range_V()
```

Alternatively you can call lower level functions `ch.set_offset_V(...)` and `ch.scale_V(...)`
(both return actually set values) and their companions `ch.get_offset_V()` and `ch.get_scale_V()`.

```python
ch3_offset_V = ch3.set_offset_V(0.0023)
ch3_V_per_div = ch3.get_scale_V(0.008)
```

#### Impedance

Channel input impedance can be set by calling function
`set_impedance_oHm(impedance_oHm: float, fail_on_error: bool = False) -> float`.
Different oscilloscopes offer different impedance values that can be set. Typically, that is 50 Ohm and 1 MOhm.
Calling this function like so is guaranteed to return actually set impedance value.

```python
ch3_impedance = ch3.set_impedance_oHm(100)
```

The above call might behave differently depending on the scope make and model. It might set impedance to the
nearest allowed value or simply reject it keeping whatever configured intact. Users can use returned value to
decide what do to about it. Alternatively call like so will ensure that requested impedance is set or error raised.

```python
ch3.set_impedance_oHm(50, fail_on_error = True)
```

List of allowed impedance values can be obtained from the `scope.properties` namespace like so

```python
allowed_impedance_values: list[float] = scope.properties.get_impedance_list()
```

Alternative to above calls is to call functions

```python
ch3_impedance = ch3.set_impedance_min()
```

or

```python
ch3_impedance = ch3.set_impedance_max()
```

which set minimum and maximum impedance value valid on a particular scope.

#### Downloading waveform

When tigger (see below) is configured and enabled on the scope, then waveform can be captured and downloaded
as a `Waveform` class like so:

```python
c1_waveform: Waveform = ch3.get_waveform()
```

Returned object (instance of `Waveform` class) will have various metadata mostly related to how it is to be rendered.
Among this metadata Waveform will have _name_. By default, name given to the waveform will be name of the channel if
channel does have a name. If channel does not have a name, but is simply referred to by a number, then waveform name
will be "_Channel $channel_number_".

To give waveform a custom name you can either call `get_waveform($name)` with `name` argument

```python
mosi_waveform: Waveform = ch3.get_waveform("mosi")
```

or set name on the already obtained waveform object

```python
from inctrl import Waveform

c1_waveform: Waveform = ch3.get_waveform()
c1_waveform.name = "mosi"
```

To ensure that you download valid waveform call `scope.trigger.wait_for_waveform(...)` method (see below).

### Trigger

Interaction with triggers consist of two parts: (a) configuring the trigger and (2) interacting with configured trigger.
All of this is available under `scope.trigger` namespace.

#### Configuration

To configure trigger call function `scope.trigger.configure(trigger: ScopeTrigger) -> None`.
Argument passed to this function is an instance of `ScopeTrigger` class corresponding to a particular trigger type.
At minimum, every oscilloscope offers edge trigger where signal capture happens on either raising or
falling edge of signal. Other triggers can trigger signal capture on pulse evens, signal patterns and so on.
At the moment we only provide code for triggering on the signal edges.

Below is a minimal edge trigger configuration, which configures scope to trigger capture on the raising edge
of signal `ch3` (that is known as _trigger source_) when it crosses 0.5 volts level.

```python
from inctrl import ScopeTrigger

scope.trigger.configure(ScopeTrigger.EDGE(trigger_source = ch3, level_V = 0.5))
```

Method `ScopeTrigger.EDGE(...)` has the following signature:

```python
def EDGE(
        trigger_source: TriggerSource,
        level_V: float,
        slope: TriggerSlope = TriggerSlope.RISING,
        delay: str | Duration = Duration.value_of("0 s")
) -> ScopeEdgeTrigger:
```

As you can see default `slope` is `TriggerSlope.RISING` but you can change to `TriggerSlope.FALLING`.
Parameter `delay` refer to position on the screen when trigger is fired. Default value of 0 seconds places trigger
position in the middle of the screen, i.e. there is a same duration of captured signal before and after trigger.
Setting delay to positive value moves trigger position to the left, i.e. there is more data points captured after
the trigger than before. Setting delay to negative value moves trigger position to the right, i.e. there is fewer
data points captured after the trigger than before.

#### Operations

Once trigger is configured you can arm the trigger to enable it. You can think of this as trigger modes.

For a single shot capture call

```python
scope.trigger.arm_single()
```

This function is non-blocking and it might time a bit of time until trigger is actually armed. To check if trigger
is armed call

```python
is_armed: bool = scope.trigger.is_armed()
```

To manually disarm trigger call

```python
scope.trigger.disarm()
```

For continuous periodic capture call

```python
scope.trigger.arm_auto()
```

For normal capture

```python
scope.trigger.arm_normal()
```

Once trigger is fired and waveforms are available they can be downloaded from the scope.
To check if waveforms are available call

```python
scope.trigger.wait_for_waveform()
```

Call like above will block indefinitely until trigger is fired and waveform is available for downloading.
Other optional arguments to this function can modify this behaviour. Signature for this function is

```python
def wait_for_waveform(
        timeout: str | Duration | None = None,
        error_on_timeout: bool = False
) -> bool
```

If `timeout` is not provided, then block wait indefinitely. If `timeout` is provided, then wait for that duration and
(if `error_on_timeout` is False (default)) return True or False if waveform is actually available for downloading, or,
if `error_on_timeout` is True, then raise RuntimeError after requested duration or return True on success.

### Examples

#### Capturing I2C data

```python
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
    delay = "20 us",

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
```


