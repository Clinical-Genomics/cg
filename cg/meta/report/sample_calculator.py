"""Contains class to calculate values on samples"""
from cg.store import models


class SampleCalculator:
    """Calculates on samples"""

    @staticmethod
    def calculate_processing_days(sample: models.Sample):
        """Calculates the days from received to delivered"""
        if sample.received_at and sample.delivered_at:
            return (sample.delivered_at - sample.received_at).days

        return None
