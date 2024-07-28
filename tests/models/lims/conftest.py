import pytest

from cg.constants.constants import CustomerId


@pytest.fixture
def lims_sample_raw() -> dict[str, str]:
    """Return a raw LIMS sample."""
    return {"name": "a_name", "container": "a_tube"}


@pytest.fixture
def lims_udfs_raw() -> dict[str, str]:
    """Return a raw LIMS UDF."""
    return {"application": "WGS", "customer": CustomerId.CUST001, "sex": "male"}


@pytest.fixture
def lims_project_raw() -> dict[str, str]:
    """Return a raw LIMS project."""
    return {"id": "an_id", "name": "a_name", "date": "2000-01-01"}
