from collections.abc import Callable
from pathlib import Path

import numpy as np
import pyarrow as pa
import pyarrow.parquet as pq
from numpy import ndarray


class Waveform:
    """
    This class holds x and y arrays representing the waveform.
    """

    def __init__(self, dx: float, trigger_index: int, ys: ndarray):
        self.__dx = dx
        self.__trigger_index = trigger_index
        self.__ys = ys
        self.__xs = np.array([(i - trigger_index) * dx for i in range(len(ys))], dtype = float)
        self.__xy = list(zip(list(self.__xs), list(self.__ys)))

    def __repr__(self):
        return f"Waveform(len = {len(self.__ys)}, dx = {self.__dx}, trigger_index = {self.__trigger_index})"

    def xy(self,
           x_predicate: Callable[[float], bool] | None = None,
           y_predicate: Callable[[float], bool] | None = None) -> tuple[ndarray, ndarray]:
        """
        Return tuple of numpy arrays. First holding values on the x-axis (time) and second on y-axis.
        Filter on predicates if any given.
        """
        return self.x(x_predicate, y_predicate), self.y(x_predicate, y_predicate)

    def x(self,
          x_predicate: Callable[[float], bool] | None = None,
          y_predicate: Callable[[float], bool] | None = None) -> ndarray:
        """ Return numpy array holding values on the x-axis (time). Filter on predicates if any given. """
        if x_predicate is not None and y_predicate is not None:
            return np.array([ab[0] for ab in self.__xy if x_predicate(ab[0]) and y_predicate(ab[1])])
        elif x_predicate is not None:
            return np.array([ab[0] for ab in self.__xy if x_predicate(ab[0])])
        elif y_predicate is not None:
            return np.array([ab[0] for ab in self.__xy if y_predicate(ab[1])])
        else:
            return self.__xs

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
        return self.__dx

    def save_to_file(self, filename: str | Path, file_format: str = "parquet") -> None:
        """ Save this waveform into a file. """
        match file_format:
            case "parquet":
                data_table = pa.table(
                    data = {"ys": self.y()},
                    metadata = {
                        "dx": f"{self.__dx}",
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
            dx = float(data_table.schema.metadata[b'dx'].decode("utf-8")),
            trigger_index = int(data_table.schema.metadata[b'trigger_index'].decode("utf-8")),
            ys = np.array(data_table.column("ys"))
        )
