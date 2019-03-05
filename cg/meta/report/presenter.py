"""Handles presentation of different data types"""
from datetime import datetime


class Presenter:
    """Contains methods for presentation of different data types"""

    @staticmethod
    def process_float_string(float_str: str, precision: int) -> str:
        """Make a float value presentable for the delivery report."""
        if float_str:
            presentable_value = str(round(float(float_str), precision))
        else:
            presentable_value = 'N/A'

        return presentable_value

    @staticmethod
    def process_string(string: str) -> str:
        """Make a string value presentable for the delivery report."""
        if string:
            presentable_value = string
        else:
            presentable_value = 'N/A'

        return presentable_value

    @staticmethod
    def process_datetime(a_date: datetime) -> str:
        """Make an date value presentable for the delivery report."""
        if a_date:
            presentable_value = str(a_date.date())
        else:
            presentable_value = 'N/A'

        return presentable_value

    @staticmethod
    def process_int(integer: int) -> str:
        """Make an integer value presentable for the delivery report."""
        if integer:
            presentable_value = str(integer)
        else:
            presentable_value = 'N/A'

        return presentable_value

    @staticmethod
    def process_set(a_set: set) -> str:
        """Make a set presentable for the delivery report."""
        if a_set:
            presentable_value = ', '.join(str(s) for s in a_set)
        else:
            presentable_value = 'N/A'

        return presentable_value

    @staticmethod
    def process_list(a_list: list):
        """Make a list presentable for the delivery report."""
        if a_list:
            presentable_value = ', '.join(str(s) for s in a_list)
        else:
            presentable_value = 'N/A'

        return presentable_value
