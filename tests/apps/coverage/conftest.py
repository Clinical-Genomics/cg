import pytest


@pytest.fixture(name="chanjo_mean_completeness")
def fixture_chanjo_mean_completeness() -> float:
    """Returns mean completeness."""
    return 100.0


@pytest.fixture(name="chanjo_mean_coverage")
def fixture_chanjo_mean_coverage() -> float:
    """Returns mean coverage."""
    return 30.0
