InCtrl - Instruments Control Python API
=======================================

_InCtrl_ library provides high level API to common electronics bench instruments, such programmable power supplies,
electronic loads, oscilloscopes and many more. Its intent is twofold. Provide API at such high level so as to minimize
cognitive load on electrical and application engineers working and the lab making lab automation easy. And second,
make it possible to write code that would use _InCtrl_ library to be agnostic to instruments makes and model where
possible, i.e. application engineers should be able to swap one equipment make for another and have their python scripts
continue running without any change. To that end interation with the instruments happens using generic handlers to
instrument types. For example, to interact with power supply user need to create an instance of `PowerSupply` class
like so

```python
from inctrl import power_supply, PowerSupply

ps: PowerSupply = power_supply("$ps_address", channel = 1)
```

Function `power_supply(...)` when called will discover make and mode of a particular power supply and return appropriate
instance of `PowerSupply`. That could be `RigolPowerSupply`, `KikusuiPowerSupply` or what have you. User does not have
to be concerned with make and model that power supply. This is of course true only up to a point. For example, you may
need power supply that can supply 100 Watts and swapping one for another might not even though API would stay the same.
To resolve this issue user can request specific capabilities that instantiating power supply my have. Details of that
can be found in other pages.

