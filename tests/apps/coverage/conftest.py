import pytest


@pytest.fixture(name="chanjo_mean_completeness")
def fixture_chanjo_mean_completeness() -> int:
    """Returns mean completeness."""
    return 100.0


@pytest.fixture(name="chanjo_mean_coverage")
def fixture_chanjo_mean_coverage() -> int:
    """Returns mean coverage."""
    return 30.0
