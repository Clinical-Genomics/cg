from cg.services.analysis_starter.configurator.models.microsalt import MicrosaltCaseConfig


def test_microsalt_get_start_command():
    # GIVEN a microSALT case config
    microsalt_case_config = MicrosaltCaseConfig(
        binary="/path/to/microsalt/binary",
        case_id="microsalt_case",
        conda_binary="/path/to/conda/binary",
        config_file="/path/to/microsalt_case/config.json",
        environment="S_microsalt",
        fastq_directory="/path/to/microsalt_case/fastq",
    )

    # WHEN getting the slurm command
    start_command: str = microsalt_case_config.get_start_command()

    # THEN the command is as expected
    expected_command = (
        f"{microsalt_case_config.conda_binary} run --name {microsalt_case_config.environment} "
        f"{microsalt_case_config.binary} analyse {microsalt_case_config.config_file} "
        f"--input {microsalt_case_config.fastq_directory}"
    )

    assert start_command == expected_command
