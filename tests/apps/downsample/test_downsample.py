"""Tests for the DownsampleAPI."""

import logging
from pathlib import Path

import pytest

from cg.apps.downsample.downsample import DownsampleAPI
from cg.meta.workflow.prepare_fastq import PrepareFastqAPI
from cg.models.cg_config import CGConfig
from cg.models.downsample.downsample_data import DownsampleData
from cg.store.models import Sample


def test_add_downsampled_case_entry_to_statusdb(
    downsample_api: DownsampleAPI, downsample_data: DownsampleData, caplog
) -> None:
    """Test to add the downsampled case entry to StatusDB."""
    # GIVEN a DownsampleAPI
    caplog.set_level(level=logging.INFO)
    # WHEN adding a downsampled case to statusDB
    downsample_api.store_downsampled_case(downsample_data)

    # THEN a downsampled case is added to the store
    assert downsample_api.status_db.get_case_by_name(downsample_data.downsampled_case.name)

    # WHEN adding the downsampled case again
    downsample_api.store_downsampled_case(downsample_data)
    # THEN a log info is added
    assert (
        f"Case with name {downsample_data.downsampled_case.name} already exists in StatusDB."
        in caplog.text
    )


def test_add_downsampled_sample_entry_to_statusdb(
    downsample_api: DownsampleAPI, downsample_data: DownsampleData
) -> None:
    """Test to add the downsampled sample entry to StatusDB."""
    # GIVEN a DownsampleAPI

    # WHEN adding a downsampled sample to statusDB
    downsample_api.store_downsampled_sample(downsample_data)

    # THEN a downsampled sample is added to the store
    assert downsample_api.status_db.get_sample_by_internal_id(
        downsample_data.downsampled_sample.internal_id
    )

    # WHEN adding the sample again

    # THEN a ValueError is raised
    with pytest.raises(ValueError):
        downsample_api.store_downsampled_sample(downsample_data)


def test_add_sample_case_links(downsample_api: DownsampleAPI, downsample_data: DownsampleData):
    """Test to link samples to cases in StatusDB."""

    # GIVEN a DownsampleAPI and a downsampled case and sample in StatusDB
    downsample_api.store_downsampled_case(downsample_data)
    downsample_api.store_downsampled_sample(downsample_data)

    # GIVEN the links are not established
    sample: Sample = downsample_api.status_db.get_sample_by_internal_id(
        downsample_data.downsampled_sample.internal_id
    )
    assert not sample.links

    # WHEN adding the sample case links
    downsample_api._link_downsampled_sample_to_case(
        downsample_data=downsample_data,
        sample=downsample_data.downsampled_sample,
        case=downsample_data.downsampled_case,
    )

    # THEN the links are established
    sample: Sample = downsample_api.status_db.get_sample_by_internal_id(
        downsample_data.downsampled_sample.internal_id
    )
    assert sample.links


def test_downsample_api_adding_a_second_sample_to_case(
    downsample_api: DownsampleAPI,
    downsample_data: DownsampleData,
    downsample_sample_internal_id_2: str,
    downsample_case_internal_id: str,
    downsample_case_name: str,
    downsample_context: CGConfig,
):
    """Test that subsequent samples are added to the given case."""
    # GIVEN a DownsampleAPI with a sample and case added
    downsample_api.store_downsampled_sample_case(downsample_data)
    downsample_context.status_db_ = downsample_api.status_db
    downsample_context.housekeeper_api_ = downsample_api.housekeeper_api

    # WHEN generating a new DownsampelData for the same case with a different sample
    new_downsample_data = DownsampleData(
        status_db=downsample_context.status_db_,
        hk_api=downsample_context.housekeeper_api_,
        sample_id=downsample_sample_internal_id_2,
        case_id=downsample_case_internal_id,
        case_name=downsample_case_name,
        number_of_reads=50,
        out_dir=Path(downsample_context.downsample.downsample_dir),
    )

    # THEN adding the sample to statusDB adds the sample and generates the links
    downsample_api.store_downsampled_sample_case(new_downsample_data)

    assert new_downsample_data.status_db.get_sample_by_internal_id(
        new_downsample_data.downsampled_sample.internal_id
    )
    assert new_downsample_data.downsampled_case.name == downsample_data.downsampled_case.name


def test_start_downsample_job(
    downsample_api: DownsampleAPI,
    downsample_sample_internal_id_1: str,
    downsample_case_internal_id: str,
    downsample_case_name: str,
    number_of_reads_in_millions: int,
    mocker,
):
    """Test that a downsample job can be started."""

    # GIVEN a DownsampleAPI
    downsample_api.dry_run = True
    # WHEN starting a downsample job
    mocker.patch.object(PrepareFastqAPI, "is_sample_decompression_needed")
    PrepareFastqAPI.is_sample_decompression_needed.return_value = False
    submitted_job: int = downsample_api.downsample_sample(
        sample_id=downsample_sample_internal_id_1,
        case_id=downsample_case_internal_id,
        case_name=downsample_case_name,
        number_of_reads=number_of_reads_in_millions,
    )

    # THEN a job is submitted
    assert submitted_job
