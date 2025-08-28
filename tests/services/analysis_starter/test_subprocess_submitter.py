import subprocess
from unittest import mock
from unittest.mock import create_autospec

import pytest

from cg.services.analysis_starter.configurator.abstract_model import CaseConfig
from cg.services.analysis_starter.configurator.models.microsalt import MicrosaltCaseConfig
from cg.services.analysis_starter.configurator.models.mip_dna import MIPDNACaseConfig
from cg.services.analysis_starter.submitters.subprocess.submitter import SubprocessSubmitter


@pytest.mark.parametrize("case_config_class", [MicrosaltCaseConfig, MIPDNACaseConfig])
def test_subprocess_submitter(case_config_class: type[SubprocessCaseConfig]):
    # GIVEN a SubProcessSubmitter
    subprocess_submitter = SubprocessSubmitter()

    # WHEN submitting a case using a valid case config
    case_config = create_autospec(case_config_class)
    case_config.get_workflow
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
