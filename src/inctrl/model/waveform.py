from collections.abc import Callable
from pathlib import Path

import numpy as np
import pyarrow as pa
import pyarrow.parquet as pq
from numpy import ndarray

from inctrl.model.time import TimeUnit


class Waveform:
    """
    This class holds x and y arrays representing the waveform.
    """

    def __init__(self, dx_s: float, trigger_index: int, ys: ndarray):
        self.__dx_s = dx_s
        self.__trigger_index = trigger_index
        self.__ys = ys
        self.__xs_s = np.array([(i - trigger_index) * dx_s for i in range(len(ys))], dtype = float)
        self.__xy = list(zip(list(self.__xs_s), list(self.__ys)))

    def __repr__(self):
        return f"Waveform(len = {len(self.__ys)}, dx = {self.__dx_s}, trigger_index = {self.__trigger_index})"

    def xy(self,
           time_unit: TimeUnit | str = TimeUnit.S,
           x_predicate: Callable[[float], bool] | None = None,
           y_predicate: Callable[[float], bool] | None = None) -> tuple[ndarray, ndarray]:
        """
        Return tuple of numpy arrays. First holding values on the x-axis (time) and second on y-axis.
        Filter on predicates if any given.
        """
        return self.x(time_unit, x_predicate, y_predicate), self.y(x_predicate, y_predicate)

    def x(self,
          time_unit: TimeUnit | str = TimeUnit.S,
          x_predicate: Callable[[float], bool] | None = None,
          y_predicate: Callable[[float], bool] | None = None) -> ndarray:
        """ Return numpy array holding values on the x-axis (time). Filter on predicates if any given. """
        requested_time_unit = TimeUnit.value_of(time_unit)
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
            ys = np.array(data_table.column("ys"))
        )

    def plot(self, time_unit: TimeUnit | str = TimeUnit.S, block: bool = True) -> None:
        from matplotlib import pyplot as plt
        fig = plt.figure(figsize = (12, 6))
        ax = fig.subplots()
        ax.grid(True)
        ax.set_xlabel(f"Time [{TimeUnit.value_of(time_unit).to_str()}]")
        ax.set_ylabel("V")
        xs, ys = self.xy(time_unit)
        fig.tight_layout()
        ax.plot(xs, ys)
        if block:
            plt.show()
        else:
            fig.show()
