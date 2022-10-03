"""Tests for chanjo coverage API."""
from pathlib import Path
from typing import Dict

from cg.apps.coverage.api import ChanjoAPI
from cg.utils.commands import Process


def test_chanjo_api_init(chanjo_config: Dict[str, Dict[str, str]]):
    """Test __init__."""
    # GIVEN a config dict

    # WHEN instantiating a chanjo API
    api = ChanjoAPI(chanjo_config)

    # THEN attributes chanjo_config and chanjo_binary are set
    assert api.chanjo_config == chanjo_config["chanjo"]["config_path"]
    assert api.chanjo_binary == chanjo_config["chanjo"]["binary_path"]


def test_chanjo_api_upload(
    bed_file: Path,
    case_id: str,
    chanjo_config: Dict[str, Dict[str, str]],
    family_name: str,
    mocker,
    sample_id: str,
    sample_name: str,
):
    """Test upload method."""
    # GIVEN sample_id, sample_name, group_id, group_name, and a bed_file

    # WHEN uploading a sample with the api, using a mocked Process.run_command method
    api = ChanjoAPI(chanjo_config)
    mocked_run_command = mocker.patch.object(Process, "run_command")
    api.upload(
        sample_id=sample_id,
        sample_name=sample_name,
        group_id=case_id,
        group_name=family_name,
        bed_file=bed_file.as_posix(),
    )

    # THEN run_command should be called with the list
    mocked_run_command.assert_called_once_with(
        parameters=[
            "load",
            "--sample",
            sample_id,
            "--name",
            sample_name,
            "--group",
            case_id,
            "--group-name",
            family_name,
            "--threshold",
            "10",
            bed_file.as_posix(),
        ]
    )


def test_chanjo_api_sample_existing(
    chanjo_config: Dict[str, Dict[str, str]],
    mocker,
    mock_process,
    sample_id: str,
):
    """Test sample method."""

    # GIVEN a sample_id

    # WHEN fetching an existing sample from the api, with a mocked stdout
    mocked_stdout = '[{"id": "%s"}]' % sample_id
    mocked_stderr = ""
    MockedProcess = mock_process(result_stderr=mocked_stderr, result_stdout=mocked_stdout)
    mocked_process = mocker.patch("cg.apps.coverage.api.Process")
    mocked_process.return_value = MockedProcess(
        binary=chanjo_config["chanjo"]["binary_path"],
        config=chanjo_config["chanjo"]["config_path"],
    )
    api = ChanjoAPI(chanjo_config)
    sample = api.sample(sample_id=sample_id)

    # THEN sample should be a dictionary with key id = sample_id
    assert sample["id"] == sample_id


def test_chanjo_api_sample_non_existing(
    chanjo_config: Dict[str, Dict[str, str]], mocker, mock_process, sample_id: str
):
    """Test sample method."""

    # GIVEN a sample_id

    # WHEN fetching a non existing sample from the api, with a mocked stdout
    mocked_stdout = "[]"
    mocked_stderr = ""
    MockedProcess = mock_process(result_stderr=mocked_stderr, result_stdout=mocked_stdout)
    mocked_process = mocker.patch("cg.apps.coverage.api.Process")
    mocked_process.return_value = MockedProcess(
        binary=chanjo_config["chanjo"]["binary_path"],
        config=chanjo_config["chanjo"]["config_path"],
    )
    api = ChanjoAPI(chanjo_config)
    sample = api.sample(sample_id=sample_id)

    # THEN None should have been returned
    assert sample is None


def test_chanjo_api_delete_sample(chanjo_config: Dict[str, Dict[str, str]], mocker, sample_id: str):
    """Test delete method."""
    # GIVEN a sample_id

    # WHEN deleting a sample with the api and a mocked Process.run_command method
    mocked_run_command = mocker.patch.object(Process, "run_command")
    api = ChanjoAPI(chanjo_config)
    api.delete_sample(sample_id=sample_id)

    # THEN run_command should be called once with list ["db", "remove", sample_id]
    mocked_run_command.assert_called_once_with(parameters=["db", "remove", sample_id])


def test_chanjo_api_omim_coverage(
    chanjo_config: Dict[str, Dict[str, str]],
    chanjo_mean_completeness: int,
    chanjo_mean_coverage: int,
    mocker,
    mock_process,
    sample_id: str,
):
    """Test omim_coverage method."""
    # GIVEN a sample_id

    # WHEN using the omim_coverage method with a mocked stdout
    mocked_stdout = '{"%s": {"mean_coverage": %f, "mean_completeness": %f}}' % (
        sample_id,
        chanjo_mean_coverage,
        chanjo_mean_completeness,
    )
    mocked_stderr = ""
    MockedProcess = mock_process(result_stderr=mocked_stderr, result_stdout=mocked_stdout)
    mocked_process = mocker.patch("cg.apps.coverage.api.Process")
    mocked_process.return_value = MockedProcess(
        binary=chanjo_config["chanjo"]["binary_path"],
        config=chanjo_config["chanjo"]["config_path"],
    )
    api = ChanjoAPI(chanjo_config)
    samples = api.omim_coverage(samples=[{"id": sample_id}])

    # THEN this should return a dictionary with mean coverage and mean_completeness
    # for each sample
    assert samples[sample_id]["mean_coverage"] == chanjo_mean_coverage
    assert samples[sample_id]["mean_completeness"] == chanjo_mean_completeness


def test_chanjo_api_coverage(
    chanjo_config: Dict[str, Dict[str, str]],
    chanjo_mean_completeness: int,
    chanjo_mean_coverage: int,
    mocker,
    mock_process,
    sample_id: str,
):
    """Test coverage method."""
    # GIVEN a sample_id

    # WHEN using the coverage method with a mocked stdout
    mocked_stdout = '{"%s": {"mean_coverage": %f, "mean_completeness": %f}}' % (
        sample_id,
        chanjo_mean_coverage,
        chanjo_mean_completeness,
    )
    mocked_stderr = ""
    MockedProcess = mock_process(result_stderr=mocked_stderr, result_stdout=mocked_stdout)
    mocked_process = mocker.patch("cg.apps.coverage.api.Process")
    mocked_process.return_value = MockedProcess(
        binary=chanjo_config["chanjo"]["binary_path"],
        config=chanjo_config["chanjo"]["config_path"],
    )
    api = ChanjoAPI(chanjo_config)
    samples = api.sample_coverage(sample_id=sample_id, panel_genes=["123"])

    # THEN this should return a dictionary with mean coverage and mean_completeness
    # the sample
    assert samples["mean_coverage"] == chanjo_mean_coverage
    assert samples["mean_completeness"] == chanjo_mean_completeness
