from cg.services.analysis_starter.configurator.models.microsalt import MicrosaltCaseConfig
from cg.services.analysis_starter.configurator.models.mip_dna import MIPDNACaseConfig


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


def test_mip_dna_get_start_command_no_flags_set():
    # GIVEN a case id
    case_id = "case_id"

    # GIVEN a MIP-DNA case config
    mip_case_config = MIPDNACaseConfig(
        conda_binary="/path/to/conda",
        conda_environment="environment",
        case_id=case_id,
        email="email@scilifelab.se",
        pipeline_binary="/path/to/pipeline/binary",
        pipeline_config_path="/path/to/pipeline/config.yaml",
        slurm_qos="normal",
        use_bwa_mem=False,
    )

    # WHEN getting the slurm command
    start_command: str = mip_case_config.get_start_command()

    # THEN the command is as expected
    expected_command = (
        f"{mip_case_config.conda_binary} run --name {mip_case_config.conda_environment} {mip_case_config.pipeline_binary} analyse rd_dna"
        f" --config {mip_case_config.pipeline_config_path} {case_id} --slurm_quality_of_service "
        f"{mip_case_config.slurm_qos} --email {mip_case_config.email}"
    )
    assert start_command == expected_command


def test_mip_dna_get_start_command_all_flags_set():
    # GIVEN a case id
    case_id = "case_id"

    # GIVEN a MIP-DNA case config
    mip_case_config = MIPDNACaseConfig(
        conda_binary="/path/to/conda",
        conda_environment="environment",
        case_id=case_id,
        email="email@scilifelab.se",
        pipeline_binary="/path/to/pipeline/binary",
        pipeline_config_path="/path/to/pipeline/config.yaml",
        slurm_qos="normal",
        start_after="retroseq_bread",
        start_with="smile_bread",
        use_bwa_mem=True,
    )

    # WHEN getting the slurm command
    start_command: str = mip_case_config.get_start_command()

    # THEN the command is as expected
    expected_command = (
        f"{mip_case_config.conda_binary} run --name {mip_case_config.conda_environment} {mip_case_config.pipeline_binary} analyse rd_dna"
        f" --config {mip_case_config.pipeline_config_path} {case_id} --slurm_quality_of_service "
        f"{mip_case_config.slurm_qos} --email {mip_case_config.email} "
        f"--start_after_recipe {mip_case_config.start_after_recipe} "
        f"--start_with_recipe {mip_case_config.start_with_recipe} "
        f"--bwa_mem 1 "
        f"--bwa_mem2 0"
    )
    assert start_command == expected_command
