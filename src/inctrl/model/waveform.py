import csv
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
           time_unit: TimeUnit | str = TimeUnit.S,
           x_predicate: Callable[[float], bool] | None = None) -> tuple[ndarray, ndarray]:
        """
        Return tuple of numpy arrays. First holding values on the x-axis (time) and second on y-axis.
        Filter on predicates if any given.
        """


class WaveformPlotter(ABC):
    def render_waveform(
            self,
            waveforms: list[WaveformProto],
            time_unit: TimeUnit,
            block: bool = True,
            dpi: int | None = None,
            to_file: str | Path | None = None
    ) -> None:
        """
        Render waveforms in the GUI framework.

        :param waveforms: list of waveforms to render
        :param time_unit: time unit to use
        :param block: True or False indicating if we want to block when rendering in GUI. Has no effect if writing file.
        :param dpi: dpi to use
        :param to_file: if provided render waveforms as PNG into a file.
        """
        pass

    @staticmethod
    @cache
    def matplotlib() -> "WaveformPlotter":
        return MatplotlibWaveformPlotter()


class MatplotlibWaveformPlotter(WaveformPlotter):
    """
    WaveformPlotter that will render waveforms using matplotlib.
    """

    def render_waveform(
            self,
            waveforms: list[WaveformProto],
            time_unit: TimeUnit,
            block: bool = True,
            dpi: int | None = None,
            to_file: str | Path | None = None) -> None:
        from matplotlib import pyplot as plt
        fig = plt.figure(figsize = (12, 8)) if dpi is None else plt.figure(figsize = (12, 8), dpi = dpi)
        ax = fig.subplots()
        ax.grid(True)

        title = ", ".join([w.name for w in waveforms])
        for waveform in waveforms:
            xs, ys = waveform.xy(time_unit)
            ax.plot(xs, ys)

        ax.set_xlabel(f"Time [{time_unit.to_str()}]")
        ax.set_ylabel("V")
        ax.set_title(title)

        fig.tight_layout()
        if to_file is not None:
            plt.savefig(to_file)
        elif block:
            plt.show(block = True)
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
        """ Waveform name. This value will be used when rendering. """
        return self.__name

    @name.setter
    def name(self, name: str) -> None:
        self.__name = name

    @override
    def xy(self,
           time_unit: TimeUnit | str = TimeUnit.S,
           x_predicate: Callable[[float], bool] | None = None) -> tuple[ndarray, ndarray]:
        """
        Return tuple of numpy arrays. First holding values on the x-axis (time) and second on y-axis.
        """
        return self.x(time_unit, x_predicate), self.y(x_predicate)

    def get_optimal_time_unit(self) -> TimeUnit:
        window_s = self.__xs_s[-1] - self.__xs_s[0]
        return Duration.value_of(f"{window_s} s").optimize().time_unit

    def x(self,
          time_unit: TimeUnit | str = TimeUnit.S,
          x_predicate: Callable[[float], bool] | None = None) -> ndarray:
        """
        Return numpy array holding values on the x-axis (time). Returned values will be in either requested time unit
        as given in argument `time_unit` or it will be derived (default) from the waveform itself.

        Filter on predicates if any given.
        """
        phys_unit_scale = TimeUnit.S.value / TimeUnit.value_of(time_unit).value

        if x_predicate is None:
            return self.__xs_s * phys_unit_scale
        else:
            return np.array([ab[0] for ab in self.__xy if x_predicate(ab[0])]) * phys_unit_scale

    def y(self, x_predicate: Callable[[float], bool] | None = None) -> ndarray:
        """ Return numpy array holding values on the y-axis (usually voltage). Filter on predicates if any given. """
        if x_predicate is None:
            return self.__ys
        else:
            return np.array([ab[1] for ab in self.__xy if x_predicate(ab[0])])

    @property
    def dt_s(self) -> float:
        """ Return time step on the t-axis in seconds. """
        return self.__dx_s

    def time_window_s(self) -> float:
        """ Return time window/domain on the t-axis in seconds. """
        return self.__xs_s[-1] - self.__xs_s[0]

    def save_to_file(self, filename: str | Path, file_format: str = "parquet") -> None:
        """ Save this waveform into a file. Including all metadata associated with this waveform. """
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

    def export_to_csv_file(
            self,
            filename: str | Path,
            time_unit: str | TimeUnit = TimeUnit.S,
            include_column_names: bool = True
    ) -> None:
        """
        Export the waveform to a csv file. Resulting file will not have any metadata such as
        implied waveform name, color for plotting etc. It will only have two columns. First column
        will contain time in requested `time_unit` (default is "seconds") and second colum the waveform
        value. If `include_column_names` is True (default is True), then the column names will also be
        included in the first row.

        Will raise Exception if unable to write into the file.
        """
        target_file = Path(filename)
        ts, ys = self.xy(time_unit = time_unit)
        with open(target_file, "w", newline = "") as file:
            writer = csv.writer(file)
            if include_column_names:
                writer.writerow(["t", "y"])
            writer.writerows(zip(ts, ys))

    def plot(self,
             plotter: WaveformPlotter = WaveformPlotter.matplotlib(),
             time_unit: TimeUnit | str | None = None,
             block: bool = True,
             dpi: int | None = None,
             to_file: str | Path | None = None) -> None:
        requested_time_unit = self.get_optimal_time_unit() if time_unit is None else TimeUnit.value_of(time_unit)
        plotter.render_waveform([self], requested_time_unit, block, dpi, to_file)

    def __mul__(self, other):
        if isinstance(other, Waveform):
            if (self.__xs_s != other.__xs_s).any():
                raise RuntimeError("These waveforms x-axis do not match")
            else:
                return Waveform(
                    dx_s = self.__dx_s, trigger_index = self.__trigger_index,
                    ys = self.__ys * other.__ys, name = self.__name
                )

        elif isinstance(other, float) or isinstance(other, int):
            return Waveform(
                dx_s = self.__dx_s, trigger_index = self.__trigger_index, ys = self.__ys * other, name = self.__name
            )

        else:
            raise RuntimeError("Waveform can only be multiplied by number or another waveform")

    def __rmul__(self, other):
        if isinstance(other, float) or isinstance(other, int):
            return Waveform(
                dx_s = self.__dx_s, trigger_index = self.__trigger_index, ys = self.__ys * other, name = self.__name
            )
        else:
            raise RuntimeError("Waveform can only be multiplied by number or another waveform")

    def __truediv__(self, scale):
        if isinstance(scale, float) or isinstance(scale, int):
            return Waveform(
                dx_s = self.__dx_s, trigger_index = self.__trigger_index, ys = self.__ys / scale, name = self.__name
            )
        else:
            raise RuntimeError("Waveform can only by divided by a number")

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


class Waveforms:
    def __init__(self, *waveforms: Waveform):
        self.waveforms = list(waveforms)

    def _get_optimal_time_unit(self) -> TimeUnit:
        time_window = self.waveforms[0].time_window_s()
        return Duration.value_of(f"{time_window} s").optimize().time_unit

    def plot(self,
             plotter: WaveformPlotter = WaveformPlotter.matplotlib(),
             time_unit: TimeUnit | str | None = None,
             block: bool = True,
             dpi: int | None = None,
             to_file: str | Path | None = None) -> None:
        requested_time_unit = self._get_optimal_time_unit() if time_unit is None else TimeUnit.value_of(time_unit)
        plotter.render_waveform(self.waveforms, requested_time_unit, block, dpi, to_file)
