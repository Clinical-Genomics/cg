from typing import Union

from cg.store import Store


class MockDB(Store):
    """Mock database"""

    def __init__(self, store):
        self.store = store


class MockChanjo:
    """Chanjo mock class"""

    def sample_coverage(self, sample_id: str, panel_genes: list) -> Union[None, dict]:
        """Calculates  for a specific panel"""

        sample_coverage = None
        if sample_id == "ADM1":
            sample_coverage = {"mean_coverage": 38.342, "mean_completeness": 99.1}
        elif sample_id == "ADM2":
            sample_coverage = {"mean_coverage": 37.342, "mean_completeness": 97.1}
        elif sample_id == "ADM3":
            sample_coverage = {"mean_coverage": 39.342, "mean_completeness": 98.1}

        return sample_coverage
