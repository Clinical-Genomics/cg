"""Handles presentation of different data types"""
from datetime import datetime


class Presenter:
    """Contains methods for presentation of different data types"""

    DEFAULT_NA = "N/A"
    DEFAULT_PRECISION = "N/A"

    def __init__(self, precision: int = DEFAULT_PRECISION, default_na: str = DEFAULT_NA):
        self._precision = precision
        self._default_na = default_na

    def process_float_string(self, raw_float_str: str, precision: int = 2) -> str:
        """Make a float value presentable"""

        return str(round(float(raw_float_str), precision)) if raw_float_str else self._default_na

    def process_float(self, raw_float: float, precision: int = 2) -> str:
        """Make a float value presentable"""

        return str(round(raw_float, precision)) if raw_float else self._default_na

    def process_string(self, raw_string: str) -> str:
        """Make a string value presentable"""

        return raw_string if raw_string else self._default_na

    def process_datetime(self, raw_date: datetime) -> str:
        """Make an date value presentable"""

        return str(raw_date.date()) if raw_date else self._default_na

    def process_int(self, raw_int: int) -> str:
        """Make an integer value presentable"""

        return str(raw_int) if raw_int else self._default_na

    def process_set(self, raw_set: set) -> str:
        """Make a set presentable"""

        return ", ".join(str(s) for s in raw_set) if raw_set else self._default_na

    def process_list(self, raw_list: list):
        """Make a list presentable"""

        if raw_list and isinstance(raw_list[0], str):
            return ", ".join(str(s) for s in raw_list) if raw_list else self._default_na

        return [self.process_obj(o) for o in raw_list]

    def process_dict(self, raw_dict: dict):
        """Make a dict presentable"""

        presentable_dict = {}
        for key, value in raw_dict.items():
            presentable_dict[key] = self.process_obj(value)

        return presentable_dict

    def process_obj(self, obj):
        """Make supported types presentable"""

        if obj is None:
            presentable_value = self._default_na
        elif isinstance(obj, str):
            if self._is_float(obj):
                presentable_value = self.process_float_string(obj)
            else:
                presentable_value = self.process_string(obj)
        elif isinstance(obj, dict):
            presentable_value = self.process_dict(obj)
        elif isinstance(obj, set):
            presentable_value = self.process_set(obj)
        elif isinstance(obj, list):
            presentable_value = self.process_list(obj)
        elif isinstance(obj, datetime):
            presentable_value = self.process_datetime(obj)
        elif isinstance(obj, int):
            presentable_value = self.process_int(obj)
        elif isinstance(obj, float):
            presentable_value = self.process_float(obj)
        else:
            raise TypeError(f"Unsupported {obj} of type {type(obj)} in {self.__class__.__name__}")

        return presentable_value

    @staticmethod
    def _is_float(value):
        try:
            float(value)
            return True
        except ValueError:
            return False
