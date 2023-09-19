"""Fixtures for testing the downsample module."""
from cg.models.downsample.downsample_meta_data import DownsampleMetaData
from cg.store import Store
from cg.store.models import Family
from tests.store_helpers import StoreHelpers


def store_with_case_and_sample_with_reads(
    store: Store,
    helpers: StoreHelpers,
) -> Store:
    """Return a store with a case and a sample with reads."""
    case: Family = helpers.add_case(name="supersonicturtle")

    for sample_internal_id in ["ACC1234567", "ACC1234568"]:
        helpers.add_sample(
            internal_id=sample_internal_id,
            customer_id=case.customer_id,
            reads=100_000_000,
        )

    return store


def number_of_reads_in_millions() -> int:
    """Return a number of reads in millions."""
    return 50
