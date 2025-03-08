from abc import ABC, abstractmethod
from collections.abc import Callable
from functools import cache
from pathlib import Path

import numpy as np
import pyarrow as pa
import pyarrow.parquet as pq
from numpy import ndarray
from typing_extensions import override

from inctrl.model.time import TimeUnit, Duration


class WaveformProto(ABC):
    @property
    @abstractmethod
    def name(self) -> str:
        """ Name of the waveform. This will be used when waveform is rendered/plotted. """

    @abstractmethod
    def xy(self,
           time_unit: TimeUnit | str | None = None,
           x_predicate: Callable[[float], bool] | None = None,
           y_predicate: Callable[[float], bool] | None = None) -> tuple[ndarray, ndarray]:
        """
        Return tuple of numpy arrays. First holding values on the x-axis (time) and second on y-axis.
        Filter on predicates if any given.
        """


class WaveformPlotter(ABC):
    def render_waveform(self, waveform: WaveformProto, time_unit: TimeUnit, block: bool = True) -> None:
        pass

    @staticmethod
    @cache
    def matplotlib() -> "WaveformPlotter":
        return MatplotlibWaveformPlotter()


class MatplotlibWaveformPlotter(WaveformPlotter):
    def render_waveform(self, waveform: WaveformProto, time_unit: TimeUnit, block: bool = True) -> None:
        from matplotlib import pyplot as plt
        fig = plt.figure(figsize = (12, 6))
        ax = fig.subplots()
        ax.grid(True)
        xs, ys = waveform.xy(time_unit)
        ax.set_xlabel(f"Time [{time_unit.to_str()}]")
        ax.set_ylabel("V")
        ax.set_title(waveform.name)
        ax.plot(xs, ys)
        fig.tight_layout()
        if block:
            plt.show()
        else:
            fig.show()


class Waveform(WaveformProto):
    """
    This class holds x and y arrays representing the waveform.
    """

    def __init__(self, dx_s: float, trigger_index: int, ys: ndarray, name: str):
        self.__dx_s = dx_s
        self.__trigger_index = trigger_index
        self.__ys = ys
        self.__xs_s = np.array([(i - trigger_index) * dx_s for i in range(len(ys))], dtype = float)
        self.__xy = list(zip(list(self.__xs_s), list(self.__ys)))
        self.__name = name

    def __repr__(self):
        return (f"Waveform({self.__name} :: len = {len(self.__ys)}, "
                f"dx = {self.__dx_s}, trigger_index = {self.__trigger_index})")

    @property
    def name(self) -> str:
        return self.__name

    @override
    def xy(self,
           time_unit: TimeUnit | str | None = None,
           x_predicate: Callable[[float], bool] | None = None,
           y_predicate: Callable[[float], bool] | None = None) -> tuple[ndarray, ndarray]:
        return self.x(time_unit, x_predicate, y_predicate), self.y(x_predicate, y_predicate)

    def _get_optimal_time_unit(self) -> TimeUnit:
        window_s = self.__xs_s[-1] - self.__xs_s[0]
        return Duration.value_of(f"{window_s} s").optimize().time_unit

    def x(self,
          time_unit: TimeUnit | str | None = None,
          x_predicate: Callable[[float], bool] | None = None,
          y_predicate: Callable[[float], bool] | None = None) -> ndarray:
        """ Return numpy array holding values on the x-axis (time). Filter on predicates if any given. """

        def get_time_unit():
            if time_unit is None:
                window_s = self.__xs_s[-1] - self.__xs_s[0]
                return Duration.value_of(f"{window_s} s").optimize().time_unit
            else:
                return TimeUnit.value_of(time_unit)

        requested_time_unit = get_time_unit()
        phys_unit_scale = TimeUnit.S.value / requested_time_unit.value

        if x_predicate is not None and y_predicate is not None:
            return np.array([ab[0] for ab in self.__xy if x_predicate(ab[0]) and y_predicate(ab[1])]) * phys_unit_scale
        elif x_predicate is not None:
            return np.array([ab[0] for ab in self.__xy if x_predicate(ab[0])]) * phys_unit_scale
        elif y_predicate is not None:
            return np.array([ab[0] for ab in self.__xy if y_predicate(ab[1])]) * phys_unit_scale
        else:
            return self.__xs_s * phys_unit_scale

    def y(self,
          x_predicate: Callable[[float], bool] | None = None,
          y_predicate: Callable[[float], bool] | None = None) -> ndarray:
        """ Return numpy array holding values on the y-axis (usually voltage). Filter on predicates if any given. """
        if x_predicate is not None and y_predicate is not None:
            return np.array([ab[1] for ab in self.__xy if x_predicate(ab[0]) and y_predicate(ab[1])])
        elif x_predicate is not None:
            return np.array([ab[1] for ab in self.__xy if x_predicate(ab[0])])
        elif y_predicate is not None:
            return np.array([ab[1] for ab in self.__xy if y_predicate(ab[1])])
        else:
            return self.__ys

    @property
    def dx(self) -> float:
        """ Return step on the x-axis. """
        return self.__dx_s

    def save_to_file(self, filename: str | Path, file_format: str = "parquet") -> None:
        """ Save this waveform into a file. """
        match file_format:
            case "parquet":
                data_table = pa.table(
                    data = {"ys": self.y()},
                    metadata = {
                        "dx": f"{self.__dx_s}",
                        "trigger_index": f"{self.__trigger_index}",
                        "name": self.__name
                    }
                )
                pq.write_table(data_table, filename, store_schema = True)
            case _:
                raise RuntimeError(f"Invalid file format \"{file_format}\"")

    @staticmethod
    def load_from_file(filename: str | Path) -> "Waveform":
        """ Load waveform from a file. """
        data_table = pq.read_table(filename)
        return Waveform(
            dx_s = float(data_table.schema.metadata[b'dx'].decode("utf-8")),
            trigger_index = int(data_table.schema.metadata[b'trigger_index'].decode("utf-8")),
            ys = np.array(data_table.column("ys")),
            name = data_table.schema.metadata[b'name'].decode("utf-8"),
        )

    def export_to_csv_file(self, filename: str | Path, time_unit: str | TimeUnit = TimeUnit.S) -> None:
        """
        Export the waveform to a csv file. Resulting file will not have any metadata such
        as implied waveform name, color for plotting etc. It will only have two columns
        "x" and "y". Column "x" will contain time in requested `time_unit` (default is seconds).
        Will raise Exception if unable to write into the file.
        """
        xs, ys = self.xy(time_unit = time_unit)
        target_file = Path(filename)
        target_file.parent.mkdir(parents = True, exist_ok = True)
        csv_text = "x,y\n" + "\n".join([f"{row[0]},{row[1]}" for row in (list(zip(xs, ys)))])
        target_file.write_text(csv_text)

    def plot(self,
             plotter: WaveformPlotter = WaveformPlotter.matplotlib(),
             time_unit: TimeUnit | str | None = None,
             block: bool = True) -> None:
        requested_time_unit = self._get_optimal_time_unit() if time_unit is None else TimeUnit.value_of(time_unit)
        plotter.render_waveform(self, requested_time_unit, block)

    def __mul__(self, other):
        if isinstance(other, float) or isinstance(other, int):
            return Waveform(
                dx_s = self.__dx_s, trigger_index = self.__trigger_index, ys = self.__ys * other, name = self.__name
            )

    def __rmul__(self, other):
        if isinstance(other, float) or isinstance(other, int):
            return Waveform(
                dx_s = self.__dx_s, trigger_index = self.__trigger_index, ys = self.__ys * other, name = self.__name
            )

    def __truediv__(self, scale):
        if isinstance(scale, float) or isinstance(scale, int):
            return Waveform(
                dx_s = self.__dx_s, trigger_index = self.__trigger_index, ys = self.__ys / scale, name = self.__name
            )

    def __add__(self, other):
        if not isinstance(other, Waveform):
            raise RuntimeError(f"Cannot add {other.__class__} to Waveform")
        elif (self.__xs_s != other.__xs_s).any():
            raise RuntimeError("These waveforms x-axis do not match")
        else:
            return Waveform(
                dx_s = self.__dx_s, trigger_index = self.__trigger_index,
                ys = self.__ys + other.__ys, name = self.__name
            )

    def __sub__(self, other):
        if not isinstance(other, Waveform):
            raise RuntimeError(f"Cannot subtract {other.__class__} from Waveform")
        else:
            return self + (-1 * other)
