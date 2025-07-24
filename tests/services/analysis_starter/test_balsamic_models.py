from pathlib import Path

import pytest

from cg.constants import SexOptions
from cg.services.analysis_starter.configurator.models.balsamic import BalsamicConfigInput


@pytest.fixture
def balsamic_config_input(tmp_path: Path) -> BalsamicConfigInput:
    return BalsamicConfigInput(
        conda_binary=tmp_path / "conda",
        balsamic_binary=tmp_path / "balsamic",
        analysis_dir=tmp_path / "analysis",
        analysis_workflow="balsamic",
        artefact_snv_observations=tmp_path / "artefact_snv.json",
        balsamic_cache=tmp_path / "cache",
        cadd_annotations=tmp_path / "cadd_annotations.json",
        cancer_germline_snv_observations=tmp_path / "cancer_germline_snv.json",
        cancer_germline_sv_observations=tmp_path / "cancer_germline_sv.json",
        cancer_somatic_snv_observations=tmp_path / "cancer_somatic_snv.json",
        cancer_somatic_sv_observations=tmp_path / "cancer_somatic_sv.json",
        case_id="test_case",
        clinical_snv_observations=tmp_path / "clinical_snv.json",
        clinical_sv_observations=tmp_path / "clinical_sv.json",
        fastq_path=tmp_path / "fastq",
        gender=SexOptions.FEMALE,
        genome_interval=tmp_path / "genome_interval.bed",
        genome_version="GRCh38",
        gens_coverage_pon=tmp_path / "gens_coverage_pon.json",
        gnomad_min_af5=tmp_path / "gnomad_min_af5.json",
        normal_sample_name="normal_sample",
        panel_bed=tmp_path / "panel.bed",
        pon_cnn=tmp_path / "pon_cnn.json",
        sentieon_install_dir=tmp_path / "sentieon",
        sentieon_license="sentieon.lic",
        soft_filter_normal=True,
        swegen_snv=tmp_path / "swegen_snv.json",
        swegen_sv=tmp_path / "swegen_sv.json",
        tumor_sample_name="tumor_sample",
    )


def test_dump_to_cli(balsamic_config_input: BalsamicConfigInput):
    """Test that the dumping of the model to a CLI string works as expected."""
    # GIVEN a BalsamicConfigInput

    # GIVEN that an optional field is None
    balsamic_config_input.gens_coverage_pon = None

    # GIVEN that a boolean field is set to True
    balsamic_config_input.soft_filter_normal = True

    # GIVEN that a boolean field is set to False
    balsamic_config_input.exome = False

    # WHEN dumping to CLI
    cli_command = balsamic_config_input.dump_to_cli()

    # THEN the command should not include the gens-coverage-pon flag
    assert "--gens-coverage-pon" not in cli_command

    # THEN the command should include the soft-filter-normal flag
    assert "--soft-filter-normal" in cli_command

    # THEN the command should not include booleans as strings
    assert "True" not in cli_command
    assert "False" not in cli_command
