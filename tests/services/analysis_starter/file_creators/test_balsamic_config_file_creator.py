from unittest.mock import Mock, create_autospec

import pytest
from pytest_mock import MockerFixture

import cg.services.analysis_starter.configurator.file_creators.balsamic_config as creator
from cg.constants import SexOptions
from cg.models.cg_config import BalsamicConfig
from cg.services.analysis_starter.configurator.file_creators.balsamic_config import (
    BalsamicConfigFileCreator,
)
from cg.store.models import Application, ApplicationVersion, Case, Sample
from cg.store.store import Store


@pytest.fixture
def expected_wgs_paired_command(balsamic_config: BalsamicConfig) -> str:
    return f"{balsamic_config.conda_binary} run {balsamic_config.binary_path} config case --analysis-dir {balsamic_config.root} --analysis-workflow balsamic --balsamic-cache {balsamic_config.balsamic_cache} --cadd-annotations {balsamic_config.root.parent} --artefact-sv-observations {balsamic_config.root.parent}/loqusdb_artefact_somatic_sv_variants_export-20250920-.vcf.gz --case-id balsamic_case_wgs_paired --fastq-path /private/var/folders/rf/t6kttqvn7zd18vy23lhz5jz80000gp/T/pytest-of-isakohlsson/pytest-2/balsamic0/balsamic_case_wgs_paired/fastq --gender female --genome-interval {balsamic_config.root.parent} --genome-version hg19 --gens-coverage-pon {balsamic_config.root.parent} --gnomad-min-af5 {balsamic_config.root.parent} --normal-sample-name sample_case_wgs_paired_normal --sentieon-install-dir {balsamic_config.root.parent} --sentieon-license 127.0.0.1:8080 --tumor-sample-name sample_case_wgs_paired_tumor"


def test_create_wgs_tumor_only(
    balsamic_config: BalsamicConfig, expected_wgs_paired_command: str, mocker: MockerFixture
):
    # GIVEN a case with one tumor WGS sample
    application: Application = create_autospec(Application, prep_category="wgs")
    application_version: ApplicationVersion = create_autospec(
        ApplicationVersion, application=application
    )
    sample_1: Sample = create_autospec(
        Sample,
        internal_id="sample_1",
        is_tumour=True,
        sex=SexOptions.FEMALE,
        application_version=application_version,
    )
    wgs_tumor_only_case: Case = create_autospec(
        Case, data_analysis="balsamic", internal_id="case_1", samples=[sample_1]
    )
    store: Store = create_autospec(Store)
    store.get_case_by_internal_id = Mock(return_value=wgs_tumor_only_case)

    # GIVEN a Lims API

    # GIVEN a BalsamicConfigFileCreator
    config_file_creator = BalsamicConfigFileCreator(
        status_db=store, lims_api=Mock(), cg_balsamic_config=balsamic_config
    )

    # GIVEN that the subprocess exits successfully
    mock_runner = mocker.patch.object(creator.subprocess, "run")

    # WHEN creating the config file
    config_file_creator.create(case_id="case_1")

    mock_runner.assert_called_once_with(
        args=expected_wgs_paired_command, check=True, shell=True, stderr=-1, stdout=-1
    )

    # # THEN the correct normal sample name should be set
    # assert cli_input.normal_sample_name is None
    #
    # # THEN the correct gens_coverage_pon should be chosen (Female)
    # assert cli_input.gens_coverage_pon == balsamic_configurator.gens_coverage_female_path
    #
    # # THEN fields not relevant for WGS analyses should be set to their default values
    # for field in PANEL_ONLY_FIELDS:
    #     assert getattr(cli_input, field) == BalsamicConfigInput.model_fields[field].default
