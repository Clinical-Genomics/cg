"""Tests for chanjo coverage api"""

from pathlib import Path

from cg.apps.coverage.api import ChanjoAPI
from cg.utils.commands import Process

CHANJO_CONFIG = {"chanjo": {"config_path": "config_path", "binary_path": "chanjo"}}


def test_chanjo_api_init():
    """Test __init__"""
    # GIVEN a config dict

    # WHEN instatiating a chanjo api
    api = ChanjoAPI(CHANJO_CONFIG)

    # THEN attributes chanjo_config and chanjo_binary are set
    assert api.chanjo_config == CHANJO_CONFIG["chanjo"]["config_path"]
    assert api.chanjo_binary == CHANJO_CONFIG["chanjo"]["binary_path"]


def test_chanjo_api_upload(mocker):
    """Test upload method"""
    # GIVEN a process with a mocked run_command method
    sample_id = "sample_id"
    sample_name = "sample_name"
    group_id = "group_id"
    group_name = "group_name"
    bed_file = "bed_file"
    mocked_run_command = mocker.patch.object(Process, "run_command")
    api = ChanjoAPI(CHANJO_CONFIG)

    # WHEN uploading a sample with the api
    api.upload(
        sample_id=sample_id,
        sample_name=sample_name,
        group_id=group_id,
        group_name=group_name,
        bed_file=bed_file,
    )

    # THEN run_command should be called with the correct arguments
    mocked_run_command.assert_called_once_with(
        [
            "load",
            "--sample",
            sample_id,
            "--name",
            sample_name,
            "--group",
            group_id,
            "--group-name",
            group_name,
            "--threshold",
            "10",
            str(bed_file),
        ]
    )


def test_chanjo_api_sample_existing(mocker, mock_process):
    """Test sample method"""

    # GIVEN a mocked process with a mocked stdout and a chanjo api
    sample_id = "sample_id"
    mocked_stdout = '[{"id": "%s"}]' % sample_id
    mocked_stderr = ""
    MockedProcess = mock_process(
        result_stderr=mocked_stderr, result_stdout=mocked_stdout
    )
    mocked_process = mocker.patch("cg.apps.coverage.api.Process")
    mocked_process.return_value = MockedProcess(
        binary=CHANJO_CONFIG["chanjo"]["binary_path"],
        config=CHANJO_CONFIG["chanjo"]["config_path"],
    )
    api = ChanjoAPI(CHANJO_CONFIG)

    # WHEN fetching an existing sample from the api
    sample = api.sample(sample_id=sample_id)

    # THEN sample should be a dictionary with key id = sample_id
    assert sample["id"] == sample_id


def test_chanjo_api_sample_non_existing(mocker, mock_process):
    """Test sample method"""

    # GIVEN a mocked process with a mocked stdout and a chanjo api
    sample_id = "sample_id"
    mocked_stdout = '[{"id": "%s"}]' % sample_id
    mocked_stderr = ""
    MockedProcess = mock_process(
        result_stderr=mocked_stderr, result_stdout=mocked_stdout
    )
    mocked_process = mocker.patch("cg.apps.coverage.api.Process")
    mocked_process.return_value = MockedProcess(
        binary=CHANJO_CONFIG["chanjo"]["binary_path"],
        config=CHANJO_CONFIG["chanjo"]["config_path"],
    )
    api = ChanjoAPI(CHANJO_CONFIG)

    # WHEN fetching a non existing sample from the api
    sample = api.sample(sample_id="non_existing")

    # THEN None should have been returned
    assert sample is None


def test_chanjo_api_delete_sample(mocker):
    """Test delete method"""
    # GIVEN a process with a mocked run_command method
    sample_id = "sample_id"
    mocked_run_command = mocker.patch.object(Process, "run_command")
    api = ChanjoAPI(CHANJO_CONFIG)

    # WHEN deleting a sample with the api
    api.delete_sample(sample_id=sample_id)

    # THEN run_command should be called with the correct arguments
    mocked_run_command.assert_called_once_with(["db", "remove", sample_id])


def test_chanjo_api_omim_coverage(mocker, mock_process):
    """Test omim_coverage method"""
    # GIVEN a mocked process with a mocked stdout and a chanjo api
    sample_id = "sample_id"
    mean_coverage = 30.0
    mean_completeness = 100.0
    mocked_stdout = '{"%s": {"mean_coverage": %f, "mean_completeness": %f}}' % (
        sample_id,
        mean_coverage,
        mean_completeness,
    )
    mocked_stderr = ""
    MockedProcess = mock_process(
        result_stderr=mocked_stderr, result_stdout=mocked_stdout
    )
    mocked_process = mocker.patch("cg.apps.coverage.api.Process")
    mocked_process.return_value = MockedProcess(
        binary=CHANJO_CONFIG["chanjo"]["binary_path"],
        config=CHANJO_CONFIG["chanjo"]["config_path"],
    )
    api = ChanjoAPI(CHANJO_CONFIG)

    # WHEN using the omim_coverage method for a list of samples
    samples = api.omim_coverage(samples=[{"id": sample_id}])

    # THEN Then this should return a dictionary with mean coverage and mean_completeness
    # for each sample
    assert samples[sample_id]["mean_coverage"] == mean_coverage
    assert samples[sample_id]["mean_completeness"] == mean_completeness


def test_chanjo_api_coverage(mocker, mock_process):
    """Test coverage method"""
    # GIVEN a mocked process with a mocked stdout and a chanjo api
    sample_id = "sample_id"
    mean_coverage = 30.0
    mean_completeness = 100.0
    mocked_stdout = '{"%s": {"mean_coverage": %f, "mean_completeness": %f}}' % (
        sample_id,
        mean_coverage,
        mean_completeness,
    )
    mocked_stderr = ""
    MockedProcess = mock_process(
        result_stderr=mocked_stderr, result_stdout=mocked_stdout
    )
    mocked_process = mocker.patch("cg.apps.coverage.api.Process")
    mocked_process.return_value = MockedProcess(
        binary=CHANJO_CONFIG["chanjo"]["binary_path"],
        config=CHANJO_CONFIG["chanjo"]["config_path"],
    )
    api = ChanjoAPI(CHANJO_CONFIG)

    # WHEN fusing the coverage method
    samples = api.sample_coverage(sample_id=sample_id, panel_genes=["123"])

    # THEN Then this should return a dictionary with mean coverage and mean_completeness
    # the sample
    assert samples["mean_coverage"] == mean_coverage
    assert samples["mean_completeness"] == mean_completeness
