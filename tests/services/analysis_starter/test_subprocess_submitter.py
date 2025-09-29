import subprocess
from unittest.mock import MagicMock

import pytest
from pytest_mock import MockerFixture

from cg.constants.priority import SlurmQos
from cg.services.analysis_starter.configurator.models.microsalt import MicrosaltCaseConfig
from cg.services.analysis_starter.configurator.models.mip_dna import MIPDNACaseConfig
from cg.services.analysis_starter.submitters.subprocess.submitter import (
    SubprocessCaseConfig,
    SubprocessSubmitter,
)


@pytest.mark.parametrize(
    "case_config",
    [
        MicrosaltCaseConfig(
            case_id="case_id",
            binary="binary",
            conda_binary="conda_binary",
            config_file="config_file",
            environment="environment",
            fastq_directory="fastq_directory",
        ),
        MIPDNACaseConfig(
            case_id="case_id",
            pipeline_binary="pipeline_binary",
            pipeline_command="analyse rd_dna",
            conda_binary="conda_binary",
            pipeline_config_path="pipeline_config_path",
            conda_environment="conda_environment",
            slurm_qos=SlurmQos.NORMAL,
            use_bwa_mem=False,
            email="my@email.se",
        ),
    ],
    ids=["microSALT", "MIP-DNA"],
)
def test_subprocess_submitter_submit(case_config: SubprocessCaseConfig, mocker: MockerFixture):
    # GIVEN a SubProcessSubmitter
    subprocess_submitter = SubprocessSubmitter()

    # GIVEN a case config with a get_start_command method

    # WHEN submitting a case using a valid case config
    mock_run: MagicMock = mocker.patch.object(subprocess, "run")
    subprocess_submitter.submit(case_config)

    # THEN the analysis should have been started
    mock_run.assert_called_once_with(
        args=case_config.get_start_command(),
        shell=True,
        check=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
    )
