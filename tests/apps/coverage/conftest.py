import pytest


@pytest.fixture
def chanjo_mean_completeness() -> float:
    """Returns mean completeness."""
    return 100.0


@pytest.fixture
def chanjo_mean_coverage() -> float:
    """Returns mean coverage."""
    return 30.0
