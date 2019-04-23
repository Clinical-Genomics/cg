"""Handles presentation of different data types"""
from datetime import datetime


class Presenter:
    """Contains methods for presentation of different data types"""

    DEFAULT = 'N/A'

    @staticmethod
    def process_float_string(float_str: str, precision: int) -> str:
        """Make a float value presentable for the delivery report."""

        return str(round(float(float_str), precision)) if float_str else Presenter.DEFAULT

    @staticmethod
    def process_string(string: str) -> str:
        """Make a string value presentable for the delivery report."""

        return string if string else Presenter.DEFAULT

    @staticmethod
    def process_datetime(a_date: datetime) -> str:
        """Make an date value presentable for the delivery report."""

        return str(a_date.date()) if a_date else Presenter.DEFAULT

    @staticmethod
    def process_int(integer: int) -> str:
        """Make an integer value presentable for the delivery report."""

        return str(integer) if integer else Presenter.DEFAULT

    @staticmethod
    def process_set(a_set: set) -> str:
        """Make a set presentable for the delivery report."""

        return ', '.join(str(s) for s in a_set) if a_set else Presenter.DEFAULT

    @staticmethod
    def process_list(a_list: list):
        """Make a list presentable for the delivery report."""

        return ', '.join(str(s) for s in a_list) if a_list else Presenter.DEFAULT
