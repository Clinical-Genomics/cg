"""Tests for the DownsampleAPI."""
import logging

import pytest

from cg.apps.downsample.downsample import DownsampleAPI
from cg.models.cg_config import CGConfig
from cg.store.models import Sample


def test_add_downsampled_case_entry_to_statusdb(downsample_api: DownsampleAPI, caplog) -> None:
    """Test to add the downsampled case entry to StatusDB."""
    # GIVEN a DownsampleAPI
    caplog.set_level(level=logging.INFO)
    # WHEN adding a downsampled case to statusDB
    downsample_api.add_downsampled_case_to_statusdb()

    # THEN a downsampled case is added to the store
    assert downsample_api.status_db.get_case_by_name(
        downsample_api.downsample_data.downsampled_case.name
    )

    # WHEN adding the downsampled case again
    downsample_api.add_downsampled_case_to_statusdb()
    # THEN a log info is added
    assert (
        f"Case with name {downsample_api.downsample_data.downsampled_case.name} already exists in StatusDB."
        in caplog.text
    )


def test_add_downsampled_sample_entry_to_statusdb(downsample_api: DownsampleAPI) -> None:
    """Test to add the downsampled sample entry to StatusDB."""
    # GIVEN a DownsampleAPI

    # WHEN adding a downsampled sample to statusDB
    downsample_api.add_downsampled_sample_entry_to_statusdb()

    # THEN a downsampled sample is added to the store
    assert downsample_api.status_db.get_sample_by_internal_id(
        downsample_api.downsample_data.downsampled_sample.internal_id
    )

    # WHEN adding the sample again

    # THEN a ValueError is raised
    with pytest.raises(ValueError):
        downsample_api.add_downsampled_sample_entry_to_statusdb()


def test_add_sample_case_links(downsample_api: DownsampleAPI):
    """Test to link samples to cases in StatusDB."""

    # GIVEN a DownsampleAPI and a downsampled case and sample in StatusDB
    downsample_api.add_downsampled_case_to_statusdb()
    downsample_api.add_downsampled_sample_entry_to_statusdb()

    # GIVEN the links are not established
    sample: Sample = downsample_api.status_db.get_sample_by_internal_id(
        downsample_api.downsample_data.downsampled_sample.internal_id
    )
    assert not sample.links

    # WHEN adding the sample case links
    downsample_api._link_downsampled_sample_to_case(
        sample=downsample_api.downsample_data.downsampled_sample,
        case=downsample_api.downsample_data.downsampled_case,
    )

    # THEN the links are established
    sample: Sample = downsample_api.status_db.get_sample_by_internal_id(
        downsample_api.downsample_data.downsampled_sample.internal_id
    )
    assert sample.links


def test_downsample_api_adding_a_second_sample_to_case(
    downsample_api: DownsampleAPI,
    downsample_sample_internal_id_2: str,
    downsample_case_internal_id: str,
    downsample_context: CGConfig,
):
    """Test that subsequent samples are added to the given case."""
    # GIVEN a DownsampleAPI with a sample and case added
    downsample_api.add_downsampled_sample_case_to_statusdb()
    downsample_context.status_db_ = downsample_api.status_db
    downsample_context.housekeeper_api_ = downsample_api.housekeeper_api

    # WHEN generating a new DownsampleAPI for the same case with a different sample
    new_downsample_api = DownsampleAPI(
        config=downsample_context,
        sample_id=downsample_sample_internal_id_2,
        case_id=downsample_case_internal_id,
        number_of_reads=50,
    )

    # THEN adding the sample to statusDB adds the sample and generates the links
    new_downsample_api.add_downsampled_sample_case_to_statusdb()

    assert new_downsample_api.status_db.get_sample_by_internal_id(
        new_downsample_api.downsample_data.downsampled_sample.internal_id
    )
    assert (
        new_downsample_api.downsample_data.downsampled_case.name
        == downsample_api.downsample_data.downsampled_case.name
    )


def test_start_downsample_job(downsample_api: DownsampleAPI, mocker):
    """Test that a downsample job can be started."""

    # GIVEN a DownsampleAPI
    downsample_api.dry_run = True
    # WHEN starting a downsample job
    mocker.patch.object(DownsampleAPI, "is_decompression_needed")
    DownsampleAPI.is_decompression_needed.return_value = False
    submitted_job: int = downsample_api.downsample_sample()

    # THEN a job is submitted
    assert submitted_job
