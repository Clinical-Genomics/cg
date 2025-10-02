from unittest.mock import Mock, create_autospec

from cg.constants import SexOptions
from cg.services.analysis_starter.configurator.file_creators.balsamic_config import (
    BalsamicConfigFileCreator,
)
from cg.store.models import Application, ApplicationVersion, Case, Sample
from cg.store.store import Store


def test_create_wgs_tumor_only():
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

    # GIVEN a BalsamicConfigFileCreator
    config_file_creator = BalsamicConfigFileCreator()

    # WHEN creating the config file
    config_file_creator.create()

    # THEN
    assert isinstance(cli_input, BalsamicConfigInput)

    # THEN the correct normal sample name should be set
    assert cli_input.normal_sample_name is None

    # THEN the correct gens_coverage_pon should be chosen (Female)
    assert cli_input.gens_coverage_pon == balsamic_configurator.gens_coverage_female_path

    # THEN fields not relevant for WGS analyses should be set to their default values
    for field in PANEL_ONLY_FIELDS:
        assert getattr(cli_input, field) == BalsamicConfigInput.model_fields[field].default
