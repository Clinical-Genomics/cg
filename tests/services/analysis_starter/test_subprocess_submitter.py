import subprocess
from unittest import mock

from cg.services.analysis_starter.configurator.models.microsalt import MicrosaltCaseConfig
from cg.services.analysis_starter.submitters.subprocess.submitter import SubprocessSubmitter


def test_subprocess_submitter():
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
            check=True,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
        )
