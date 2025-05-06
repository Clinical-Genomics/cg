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
            "/path/to/conda/binary run --name S_microsalt "
            "/path/to/microsalt/binary analyse /path/to/microsalt_case/config.json "
            "--input /path/to/microsalt_case/fastq"
        )
        mock_run.assert_called_once_with(
            args=expected_args,
            shell=True,
            check=False,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
        )
