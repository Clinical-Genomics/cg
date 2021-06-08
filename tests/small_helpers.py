"""Class with small helper functions"""

from typing import Iterable


class SmallHelpers:
    """Hold small methods that might be helpful for the tests"""

    @staticmethod
    def length_of_iterable(iter_obj: Iterable) -> int:
        """Returns the length of an iterable"""
        return sum(1 for _ in iter_obj)

    def get_sample_attribute(self, lims_id: str, key: str):
        udfs = {
            "original_lab_address": "171 76 Stockholm, Sweden",
            "original_lab": "Karolinska University Hospital",
            "region_code": "01",
            "collection_date": "2020-11-22",
            "region": "Stockholm",
        }
        return udfs[key]
