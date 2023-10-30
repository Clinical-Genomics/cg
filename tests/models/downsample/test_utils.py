"""Tests for the DownsampleData utility functions."""
from cg.apps.downsample.utils import case_exists_in_statusdb, sample_exists_in_statusdb
from cg.store import Store


def test_case_exists_in_statusdb(
    store_with_case_and_sample_with_reads: Store, downsample_case_internal_id: str
):
    # GIVEN a store with a case and a sample

    # WHEN checking if a case that is in the store exists
    does_exist: bool = case_exists_in_statusdb(
        status_db=store_with_case_and_sample_with_reads, case_id=downsample_case_internal_id
    )
    # THEN the case does exist
    assert does_exist


def test_case_does_not_exist_in_statusdb(
    store_with_case_and_sample_with_reads: Store,
):
    # GIVEN a store with a case

    # WHEN checking if a case that is not in the store exists
    does_exist: bool = case_exists_in_statusdb(
        status_db=store_with_case_and_sample_with_reads, case_id="does_not_exist"
    )
    # THEN the case does not exist
    assert not does_exist


def test_sample_does_exist_in_statusdb(
    store_with_case_and_sample_with_reads: Store, downsample_sample_internal_id_1: str
):
    # GIVEN a store with a sample

    # WHEN checking if a sample that is in the store exists
    does_exist: bool = sample_exists_in_statusdb(
        status_db=store_with_case_and_sample_with_reads, sample_id=downsample_sample_internal_id_1
    )

    # THEN the sample does exist
    assert does_exist


def test_sample_does_not_exist_in_statusdb(store_with_case_and_sample_with_reads: Store):
    # GIVEN a store with a sample

    # WHEN checking if a sample that is not in the store exists
    does_exist: bool = sample_exists_in_statusdb(
        status_db=store_with_case_and_sample_with_reads, sample_id="does_not_exist"
    )

    # THEN the sample does not exist
    assert not does_exist
