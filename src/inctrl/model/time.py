from typing import Any


class Duration:
    def __init__(self, duration: str):
        self.duration = duration

    @staticmethod
    def value_of(s: Any) -> "Duration":
        if isinstance(s, Duration):
            return s
        else:
            return Duration(f"{s}")
