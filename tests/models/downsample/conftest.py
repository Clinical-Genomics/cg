"""Fixtures for testing the downsample module."""
from pathlib import Path
from typing import Dict

import pytest

from cg.apps.housekeeper.hk import HousekeeperAPI
from cg.constants import SequencingFileTag
from cg.models.downsample.downsample_meta_data import DownsampleMetaData
from cg.store import Store
from cg.store.models import Family, Sample
from tests.store_helpers import StoreHelpers


@pytest.fixture()
def store_with_case_and_sample_with_reads(
    store: Store,
    helpers: StoreHelpers,
    downsample_case_internal_id: str,
    downsample_sample_internal_id_1: str,
    downsample_sample_internal_id_2: str,
) -> Store:
    """Return a store with a case and a sample with reads."""
    case: Family = helpers.add_case(store=store, internal_id=downsample_case_internal_id)

    for sample_internal_id in [downsample_sample_internal_id_1, downsample_sample_internal_id_2]:
        helpers.add_sample(
            store=store,
            internal_id=sample_internal_id,
            customer_id=case.customer_id,
            reads=100_000_000,
        )
        sample: Sample = store.get_sample_by_internal_id(internal_id=sample_internal_id)
        helpers.add_relationship(store=store, case=case, sample=sample)

    return store


@pytest.fixture()
def downsample_case_internal_id() -> str:
    """Return a case internal id."""
    return "supersonicturtle"


@pytest.fixture()
def downsample_sample_internal_id_1() -> str:
    """Return a sample internal id."""
    return "ACC1234567"


@pytest.fixture()
def downsample_sample_internal_id_2() -> str:
    """Return a sample internal id."""
    return "ACC1234568"


@pytest.fixture()
def number_of_reads_in_millions() -> int:
    """Return a number of reads in millions."""
    return 50


@pytest.fixture()
def downsample_hk_api(
    real_housekeeper_api: HousekeeperAPI,
    fastq_file: Path,
    downsample_sample_internal_id_1: str,
    downsample_sample_internal_id_2: str,
    timestamp_yesterday: str,
    helpers: StoreHelpers,
) -> HousekeeperAPI:
    """Return a Housekeeper API with a real database."""
    for sample_internal_id in [downsample_sample_internal_id_1, downsample_sample_internal_id_2]:
        downsample_bundle: Dict = {
            "name": sample_internal_id,
            "created": timestamp_yesterday,
            "expires": timestamp_yesterday,
            "files": [
                {
                    "path": fastq_file.as_posix(),
                    "archive": False,
                    "tags": [SequencingFileTag.FASTQ, sample_internal_id],
                }
            ],
        }
        helpers.ensure_hk_bundle(store=real_housekeeper_api, bundle_data=downsample_bundle)
    return real_housekeeper_api
