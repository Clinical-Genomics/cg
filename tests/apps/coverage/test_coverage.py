"""Tests for chanjo coverage api"""

from pathlib import Path

from cg.apps.coverage.api import ChanjoAPI
from cg.utils.commands import Process


def test_chanjo_api_init(chanjo_config_dict):
    """Test __init__"""
    # GIVEN a config dict

    # WHEN instatiating a chanjo api
    api = ChanjoAPI(chanjo_config_dict)

    # THEN attributes chanjo_config and chanjo_binary are set
    assert api.chanjo_config == chanjo_config_dict["chanjo"]["config_path"]
    assert api.chanjo_binary == chanjo_config_dict["chanjo"]["binary_path"]


def test_chanjo_api_upload(chanjo_config_dict, mocker):
    """Test upload method"""
    # GIVEN sample_id, sample_name, group_id, group_name, and a bed_file
    sample_id = "sample_id"
    sample_name = "sample_name"
    group_id = "group_id"
    group_name = "group_name"
    bed_file = "bed_file"

    # WHEN uploading a sample with the api, using a mocked Process.run_command method
    api = ChanjoAPI(chanjo_config_dict)
    mocked_run_command = mocker.patch.object(Process, "run_command")
    api.upload(
        sample_id=sample_id,
        sample_name=sample_name,
        group_id=group_id,
        group_name=group_name,
        bed_file=bed_file,
    )

    # THEN run_command should be called with the list
    # ["load", "--sample", sample_id, "--name", sample_name, "--group", group_id,
    #  "--group_name", group_name, "--threshold", "10", bed_file]
    mocked_run_command.assert_called_once_with(
        parameters=[
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
            bed_file,
        ]
    )


def test_chanjo_api_sample_existing(chanjo_config_dict, mocker, mock_process):
    """Test sample method"""

    # GIVEN a sample_id
    sample_id = "sample_id"

    # WHEN fetching an existing sample from the api, with a mocked stdout
    mocked_stdout = '[{"id": "%s"}]' % sample_id
    mocked_stderr = ""
    MockedProcess = mock_process(result_stderr=mocked_stderr, result_stdout=mocked_stdout)
    mocked_process = mocker.patch("cg.apps.coverage.api.Process")
    mocked_process.return_value = MockedProcess(
        binary=chanjo_config_dict["chanjo"]["binary_path"],
        config=chanjo_config_dict["chanjo"]["config_path"],
    )
    api = ChanjoAPI(chanjo_config_dict)
    sample = api.sample(sample_id=sample_id)

    # THEN sample should be a dictionary with key id = sample_id
    assert sample["id"] == sample_id


def test_chanjo_api_sample_non_existing(chanjo_config_dict, mocker, mock_process):
    """Test sample method"""

    # GIVEN a sample_id
    sample_id = "sample_id"

    # WHEN fetching a non existing sample from the api, with a mocked stdout
    mocked_stdout = "[]"
    mocked_stderr = ""
    MockedProcess = mock_process(result_stderr=mocked_stderr, result_stdout=mocked_stdout)
    mocked_process = mocker.patch("cg.apps.coverage.api.Process")
    mocked_process.return_value = MockedProcess(
        binary=chanjo_config_dict["chanjo"]["binary_path"],
        config=chanjo_config_dict["chanjo"]["config_path"],
    )
    api = ChanjoAPI(chanjo_config_dict)
    sample = api.sample(sample_id=sample_id)

    # THEN None should have been returned
    assert sample is None


def test_chanjo_api_delete_sample(chanjo_config_dict, mocker):
    """Test delete method"""
    # GIVEN a sample_id
    sample_id = "sample_id"

    # WHEN deleting a sample with the api and a mocked Process.run_command method
    mocked_run_command = mocker.patch.object(Process, "run_command")
    api = ChanjoAPI(chanjo_config_dict)
    api.delete_sample(sample_id=sample_id)

    # THEN run_command should be called once with list ["db", "remove", sample_id]
    mocked_run_command.assert_called_once_with(parameters=["db", "remove", sample_id])


def test_chanjo_api_omim_coverage(chanjo_config_dict, mocker, mock_process):
    """Test omim_coverage method"""
    # GIVEN a sample_id
    sample_id = "sample_id"

    # WHEN using the omim_coverage method with a mocked stdout
    mean_coverage = 30.0
    mean_completeness = 100.0
    mocked_stdout = '{"%s": {"mean_coverage": %f, "mean_completeness": %f}}' % (
        sample_id,
        mean_coverage,
        mean_completeness,
    )
    mocked_stderr = ""
    MockedProcess = mock_process(result_stderr=mocked_stderr, result_stdout=mocked_stdout)
    mocked_process = mocker.patch("cg.apps.coverage.api.Process")
    mocked_process.return_value = MockedProcess(
        binary=chanjo_config_dict["chanjo"]["binary_path"],
        config=chanjo_config_dict["chanjo"]["config_path"],
    )
    api = ChanjoAPI(chanjo_config_dict)
    samples = api.omim_coverage(samples=[{"id": sample_id}])

    # THEN Then this should return a dictionary with mean coverage and mean_completeness
    # for each sample
    assert samples[sample_id]["mean_coverage"] == mean_coverage
    assert samples[sample_id]["mean_completeness"] == mean_completeness


def test_chanjo_api_coverage(chanjo_config_dict, mocker, mock_process):
    """Test coverage method"""
    # GIVEN a sample_id
    sample_id = "sample_id"

    # WHEN using the coverage method with a mocked stdout
    mean_coverage = 30.0
    mean_completeness = 100.0
    mocked_stdout = '{"%s": {"mean_coverage": %f, "mean_completeness": %f}}' % (
        sample_id,
        mean_coverage,
        mean_completeness,
    )
    mocked_stderr = ""
    MockedProcess = mock_process(result_stderr=mocked_stderr, result_stdout=mocked_stdout)
    mocked_process = mocker.patch("cg.apps.coverage.api.Process")
    mocked_process.return_value = MockedProcess(
        binary=chanjo_config_dict["chanjo"]["binary_path"],
        config=chanjo_config_dict["chanjo"]["config_path"],
    )
    api = ChanjoAPI(chanjo_config_dict)
    samples = api.sample_coverage(sample_id=sample_id, panel_genes=["123"])

    # THEN Then this should return a dictionary with mean coverage and mean_completeness
    # the sample
    assert samples["mean_coverage"] == mean_coverage
    assert samples["mean_completeness"] == mean_completeness
