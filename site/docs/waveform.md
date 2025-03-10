Waveform
========

When using oscilloscope you can download waveform for any given channel by calling `channel.get_waveform()` method.
On this page we will outline what you can do with the waveform object.

### Accessing x-y values

Functions `Waveform::x(...)`, `Waveform::x(...)` and `Waveform::xy(...)` are used to access x-y values of the waveform.
Function `xy(...)` is a superset of the other two. Hence, we will talk just about this function. The same concepts will
be applicable to the `x(...)` and `y(...)` functions.

By default, simply calling `waveform.xy()` return tuple of numpy ndarrays for the whole of the trace.
First one holding x-axis values in unit of seconds and second y-axis values (usually that is voltage).

```python
ts, ys = waveform.xy()
```

You can request different time units on the x-axis. For example in microseconds:

```python
ts, ys = waveform.xy("us")
```

or

```python
from inctrl import TimeUnit

ts, ys = waveform.xy(TimeUnit.US)
```

You can indicate time unit as either a string using usual unit notation (`"s"` for seconds, `"ms"` for
milliseconds and so on) or pass `TimeUnit` enum value.

Time 0 corresponds to the moment of when trigger is fired. To see part of the waveform after the trigger you can pass
`x_predicate` filter argument like so:

```python
ts, ys = waveform.xy(x_predicate = lambda t: t >= 0)
```

Note that `x_predicate` function will always receive time in seconds, independently of the requested time unit.
Thus following two calls return the same arrays.

```python
ts, ys = waveform.xy(time_unit = TimeUnit.US, x_predicate = lambda t: t >= 0.003)

ts, ys = waveform.xy(time_unit = TimeUnit.MS, x_predicate = lambda t: t >= 0.003)
```

### Math operations

#### Scaling

Waveform can be multiplied or divided by a number producing new scaled waveform. For example:

```python
w2 = waveform * 2

w_half = waveform / 2
```

### Add, subtract, multiply

Two waveforms that have exactly the same values on the x-axis can be added, subtracted or multiplied.

```python
waveform1 * waveform2
```

### Changing waveform metadata

Some of the waveform metadata can be changed. In particular waveform has a name derived from either a channel name
or when waveform if obtained by calling `channel.get_waveform(name = "$name")`. This name is used for plotting waveform.

You can change it like so

```python
waveform.name = "Vout"
```

### Saving into a file

Waveform can be saved into a file together with all of its metadata like so

```python
waveform.save_to_file("waveform.wfm")
```

This will save it in compact binary form using [parquet](https://parquet.apache.org/) data format.

It can then be loaded like so

```python
waveform = Waveform.load_from_file("waveform.wfm")
```

### Exporting into csv

X and Y values for a waveform can be exported into a csv file like so

```python
waveform.export_to_csv_file("waveform.csv")
```

In this format no metadata will be stored in the resulting file, online time and voltage values.
By default, resulting csv file will include a header (first row) identifying column names, these will be
strings `"t"` and `"y"`. This header can be excluded like so

```python
waveform.export_to_csv_file("waveform.csv", include_column_names = False)
```

Time column will be in seconds but can overridden like so

```python
waveform.export_to_csv_file("waveform.csv", time_unit = "us", include_column_names = False)
```

or

```python
waveform.export_to_csv_file("waveform.csv", time_unit = TimeUnit.US, include_column_names = False)
```

### Plotting

If optional [matplotlib](https://matplotlib.org/) library is installed then waveform can be plotted and shown
in GUI window like so

```python
waveform.plot()
```

This call will block until plot window is closed, unless optional `block` argument is set to `False`

```python
waveform.plot(block = False)
```

By default, time unit on the x-axis will be set automatically to provide most compact representation for time values.
It can, however, be overridden like so:

```python
waveform.plot(time_unit = "ms")

waveform.plot(time_unit = TimeUnit.MS)
```

To generate image png file, pass `to_file` argument like so

```python
waveform.plot(to_file = "waveform.png")
```

When called like so this call never blocks independently value assigned to `block` argument.

Writing into png file will use default DPI (dots per inch) value as set in matplotlib, but can be overridden
by supplying `dpi` argument like so:

```python
waveform.plot(to_file = "waveform.png", dpi = 600)
```

Note, that DPI value will affect image size.
