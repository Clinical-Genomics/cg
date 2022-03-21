from typing import Union

from cg.store import Store


class MockDB(Store):
    """Mock database"""

    def __init__(self, store):
        self.store = store


class MockChanjo:
    """Chanjo mock class"""

    _sample_coverage_returns_none = False

    def sample_coverage(self, sample_id: str, panel_genes: list) -> Union[None, dict]:
        """Calculate coverage for OMIM panel"""

        if self._sample_coverage_returns_none:
            return None
        elif sample_id == "ADM1":
            output = {"mean_coverage": 38.342, "mean_completeness": 99.1}
        elif sample_id == "ADM2":
            output = {"mean_coverage": 37.342, "mean_completeness": 97.1}
        else:
            output = {"mean_coverage": 39.342, "mean_completeness": 98.1}

        return output


class MockScout:
    """Scout Mock API"""

    def get_genes(self, panel_id: str, build: str = None) -> list:
        return []
