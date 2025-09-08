import subprocess
from unittest import mock
from unittest.mock import create_autospec

from pytest_mock import MockerFixture

from cg.services.analysis_starter.configurator.models.microsalt import MicrosaltCaseConfig
from cg.services.analysis_starter.submitters.subprocess.submitter import SubprocessSubmitter


def test_microsalt_submit():
    # GIVEN a SubProcessSubmitter
    subprocess_submitter = SubprocessSubmitter()

    # WHEN submitting a case using a valid case config
    microsalt_case_config = MicrosaltCaseConfig(
        binary="/path/to/microsalt/binary",
        case_id="microsalt_case",
        conda_binary="/path/to/conda/binary",
        config_file="/path/to/microsalt_case/config.json",
        environment="S_microsalt",
        fastq_directory="/path/to/microsalt_case/fastq",
    )
    with mock.patch.object(subprocess, "run") as mock_run:
        subprocess_submitter.submit(microsalt_case_config)

        # THEN the analysis should have been started
        expected_args = (
            f"{microsalt_case_config.conda_binary} run --name {microsalt_case_config.environment} "
            f"{microsalt_case_config.binary} analyse {microsalt_case_config.config_file} "
            f"--input {microsalt_case_config.fastq_directory}"
        )
        mock_run.assert_called_once_with(
            args=expected_args,
            shell=True,
            check=False,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
        )


def test_microsalt_get_workflow_version(mocker: MockerFixture):
    # GIVEN a SubprocessSubmitter
    subprocess_submitter = SubprocessSubmitter()

    # GIVEN a microSALT case config
    case_config = MicrosaltCaseConfig(
        case_id="case_id",
        binary="binary",
        conda_binary="conda_binary",
        config_file="microSALT.yml",
        environment="S_microSALT",
        fastq_directory="fastq/dir",
    )

    # GIVEN that running a subprocess works
    mocker.patch.object(
        subprocess,
        "run",
        return_value=create_autospec(
            subprocess.CompletedProcess, stdout=b"microSALT, version 4.2.2 \n"
        ),
    )

    # WHEN getting the workflow version
    workflow_version = subprocess_submitter.get_workflow_version(case_config)

    # THEN the workflow version should have been returned
    assert workflow_version == "4.2.2"
