from pathlib import Path
from unittest.mock import Mock, create_autospec

import pytest

from cg.constants import SexOptions
from cg.constants.priority import SlurmQos
from cg.exc import BalsamicMissingTumorError, BedFileNotFoundError, CaseNotConfiguredError
from cg.services.analysis_starter.configurator.implementations.balsamic import BalsamicConfigurator
from cg.services.analysis_starter.configurator.models.balsamic import (
    BalsamicCaseConfig,
    BalsamicConfigInput,
)
from cg.store.models import Application, ApplicationVersion, BedVersion, Case, Sample

PANEL_ONLY_FIELDS = ["soft_filter_normal", "panel_bed", "pon_cnn", "exome"]
WGS_ONLY_FIELDS = ["genome_interval", "gens_coverage_pon"]


def test_get_pon_file(balsamic_configurator: BalsamicConfigurator, tmp_path: Path):
    # GIVEN a Balsamic configurator
    balsamic_configurator.pon_directory = tmp_path
    # GIVEN a bed file
    panel_name = "GMS_duck"
    bed_file = Path(balsamic_configurator.bed_directory, f"{panel_name}.bed")

    # GIVEN two matching PON files
    old_pon_path = Path(tmp_path, f"{panel_name}_CNVkit_PON_reference_v1.cnn")
    new_pon_path = Path(tmp_path, f"{panel_name}_CNVkit_PON_reference_v2.cnn")
    for pon_path in [old_pon_path, new_pon_path]:
        pon_path.touch()

    # WHEN getting the pon path
    pon_path: Path = balsamic_configurator._get_pon_file(bed_file)

    # THEN the returned path should be the latest version
    assert pon_path == new_pon_path


def test_get_pon_file_no_match(balsamic_configurator: BalsamicConfigurator, tmp_path: Path):
    # GIVEN a Balsamic configurator
    balsamic_configurator.pon_directory = tmp_path

    # GIVEN a bed file with no matching PON files
    panel_name = "GMS_duck"
    bed_file = Path(balsamic_configurator.bed_directory, f"{panel_name}.bed")

    # WHEN getting the pon path
    # THEN it should raise a FileNotFoundError
    with pytest.raises(FileNotFoundError):
        balsamic_configurator._get_pon_file(bed_file)


def test_get_patient_sex():
    """Tests that the correct sex is returned when all samples have the same sex"""
    # GIVEN a case with two samples
    case_with_male = create_autospec(Case)

    # GIVEN that the samples have the same sex
    sample1 = create_autospec(Sample, sex=SexOptions.MALE)
    sample2 = create_autospec(Sample, sex=SexOptions.MALE)
    case_with_male.samples = [sample1, sample2]

    # WHEN getting the sex
    sex = BalsamicConfigurator._get_patient_sex(case_with_male)

    # THEN the correct sex should be returned
    assert sex == SexOptions.MALE


def test_resolve_bed_file_correct_in_lims(balsamic_configurator: BalsamicConfigurator):
    """Test that the correct bed file is resolved when it exists in LIMS."""
    # GIVEN a Balsamic configurator with a bed_directory
    bed_directory = Path("path/to/bed/files")
    balsamic_configurator.bed_directory = bed_directory

    # GIVEN a case with a sample
    case_with_bed = create_autospec(Case)
    sample = create_autospec(Sample, internal_id="sample1")
    case_with_bed.samples = [sample]

    # GIVEN that the sample has a panel set in LIMS
    balsamic_configurator.lims_api.capture_kit = Mock(return_value="GMS_duck")

    # GIVEN that the panel exists in the store
    balsamic_configurator.store.get_bed_version_by_short_name = Mock(
        return_value=create_autospec(BedVersion, filename="GMS_duck_v5.99_extra_floating.bed")
    )

    # WHEN resolving the bed file
    bed_file = balsamic_configurator._resolve_bed_file(case_with_bed)

    # THEN the correct bed file should be returned
    assert bed_file == Path(bed_directory, "GMS_duck_v5.99_extra_floating.bed")


def test_resolve_bed_file_not_in_lims(balsamic_configurator: BalsamicConfigurator):
    """Test that an error is raised when the panel is not set in LIMS."""
    # GIVEN a Balsamic configurator with a bed_directory
    bed_directory = Path("path/to/bed/files")
    balsamic_configurator.bed_directory = bed_directory

    # GIVEN a case with a sample
    case_missing_bed = create_autospec(Case)
    sample = create_autospec(Sample, internal_id="sample1")
    case_missing_bed.samples = [sample]

    # GIVEN that the sample does not have a panel set in LIMS
    balsamic_configurator.lims_api.capture_kit = Mock(return_value=None)

    # WHEN resolving the bed file
    # THEN it should raise a ValueError
    with pytest.raises(BedFileNotFoundError):
        balsamic_configurator._resolve_bed_file(case_missing_bed)


def test_resolve_bed_file_not_in_store(balsamic_configurator: BalsamicConfigurator):
    """Test that an error is raised when the panel does not exist in the store."""
    # GIVEN a Balsamic configurator with a bed_directory
    bed_directory = Path("path/to/bed/files")
    balsamic_configurator.bed_directory = bed_directory

    # GIVEN a case with a sample
    case_missing_bed = create_autospec(Case)
    sample = create_autospec(Sample, internal_id="sample1")
    case_missing_bed.samples = [sample]

    # GIVEN that the sample has a panel set in LIMS
    balsamic_configurator.lims_api.capture_kit = Mock(return_value="GMS_duck")

    # GIVEN that the panel does not exist in the store
    balsamic_configurator.store.get_bed_version_by_short_name = Mock(return_value=None)

    # WHEN resolving the bed file
    # THEN it should raise a ValueError
    with pytest.raises(BedFileNotFoundError):
        balsamic_configurator._resolve_bed_file(case_missing_bed)


def test_resolve_bed_file_override_with_flag(balsamic_configurator: BalsamicConfigurator):
    """Test that the bed file can be overridden with a flag."""
    # GIVEN a Balsamic configurator with a bed_directory
    bed_directory = Path("path/to/bed/files")
    balsamic_configurator.bed_directory = bed_directory

    # GIVEN a case with a sample
    case_missing_bed = create_autospec(Case)
    sample = create_autospec(Sample, internal_id="sample1")
    case_missing_bed.samples = [sample]

    # GIVEN that the sample has a panel set in LIMS
    balsamic_configurator.lims_api.capture_kit = Mock(return_value=None)

    # GIVEN that the panel exists in the store
    balsamic_configurator.store.get_bed_version_by_short_name = Mock(
        return_value=create_autospec(BedVersion, filename="NACG_goose_1_99_max_fluff.bed")
    )

    # WHEN resolving the bed file with an override flag
    provided_bed_name = Path("NACG_goose")
    bed_file = balsamic_configurator._resolve_bed_file(
        case_missing_bed, panel_bed=provided_bed_name
    )

    # THEN the overridden bed file should be returned
    assert bed_file == Path(bed_directory, "NACG_goose_1_99_max_fluff.bed")

    # THEN the LIMS API should not be called
    balsamic_configurator.lims_api.capture_kit.assert_not_called()


def test_get_normal_sample_id():
    """Tests that a case containing a normal sample returns the correct sample id."""
    # GIVEN a case with a normal sample
    case_with_normal = create_autospec(Case)
    normal_sample = create_autospec(Sample, internal_id="normal_sample", is_tumour=False)
    case_with_normal.samples = [normal_sample]

    # WHEN getting the normal sample id
    normal_sample_id = BalsamicConfigurator._get_normal_sample_id(case_with_normal)

    # THEN the correct normal sample id should be returned
    assert normal_sample_id == "normal_sample"


def test_get_normal_sample_id_no_normal_sample():
    """Tests that a case without a normal returns None."""
    # GIVEN a case without a normal sample
    case_with_tumor = create_autospec(Case)
    tumour_sample = create_autospec(Sample, internal_id="tumour_sample", is_tumour=True)
    case_with_tumor.samples = [tumour_sample]

    # WHEN getting the normal sample id
    normal_sample_id = BalsamicConfigurator._get_normal_sample_id(case_with_tumor)

    # THEN the normal sample id should be None
    assert normal_sample_id is None


def test_get_tumor_sample_id():
    """Tests that a case containing a tumor sample returns the correct sample id."""
    # GIVEN a case with a tumor sample
    case_with_tumor = create_autospec(Case)
    tumor_sample = create_autospec(Sample, internal_id="tumor_sample", is_tumour=True)
    case_with_tumor.samples = [tumor_sample]

    # WHEN getting the tumor sample id
    tumor_sample_id = BalsamicConfigurator._get_tumor_sample_id(case_with_tumor)

    # THEN the correct tumor sample id should be returned
    assert tumor_sample_id == "tumor_sample"


def test_get_tumor_sample_id_no_tumor_sample():
    """Tests that a case without tumor samples raises an error."""
    # GIVEN a case without a tumor sample
    case_with_normal = create_autospec(Case)
    normal_sample = create_autospec(Sample, internal_id="normal_sample", is_tumour=False)
    case_with_normal.samples = [normal_sample]

    # WHEN getting the tumor sample id
    # THEN it should raise a ValueError
    with pytest.raises(BalsamicMissingTumorError):
        BalsamicConfigurator._get_tumor_sample_id(case_with_normal)


def test_build_cli_input_wgs_tumor_only(balsamic_configurator: BalsamicConfigurator):
    # GIVEN a case with one tumor WGS sample
    wgs_tumor_only_case = create_autospec(Case, data_analysis="balsamic", internal_id="case_1")
    application = create_autospec(Application, prep_category="wgs")
    application_version = create_autospec(ApplicationVersion, application=application)
    sample_1 = create_autospec(
        Sample,
        internal_id="sample_1",
        is_tumour=True,
        sex=SexOptions.FEMALE,
        application_version=application_version,
    )
    wgs_tumor_only_case.samples = [sample_1]
    balsamic_configurator.store.get_case_by_internal_id = Mock(return_value=wgs_tumor_only_case)

    # WHEN building the CLI input
    cli_input: BalsamicConfigInput = balsamic_configurator._build_cli_input(
        case_id=wgs_tumor_only_case.internal_id
    )

    # THEN pydantic model should be created (and validated)
    assert isinstance(cli_input, BalsamicConfigInput)

    # THEN the correct normal sample name should be set
    assert cli_input.normal_sample_name is None

    # THEN the correct gens_coverage_pon should be chosen (Female)
    assert cli_input.gens_coverage_pon == balsamic_configurator.gens_coverage_female_path

    # THEN fields not relevant for WGS analyses should be set to their default values
    for field in PANEL_ONLY_FIELDS:
        assert getattr(cli_input, field) == BalsamicConfigInput.model_fields[field].default


def test_build_cli_input_wgs_tumor_normal(balsamic_configurator: BalsamicConfigurator):
    # GIVEN a case with two WGS samples (tumor and normal)
    wgs_tumor_only_case = create_autospec(Case, data_analysis="balsamic-umi", internal_id="case_1")
    application = create_autospec(Application, prep_category="wgs")
    application_version = create_autospec(ApplicationVersion, application=application)
    sample_1 = create_autospec(
        Sample,
        internal_id="tumor_sample",
        is_tumour=True,
        sex=SexOptions.MALE,
        application_version=application_version,
    )
    sample_2 = create_autospec(
        Sample,
        internal_id="normal_sample",
        is_tumour=False,
        sex=SexOptions.MALE,
        application_version=application_version,
    )
    wgs_tumor_only_case.samples = [sample_1, sample_2]
    balsamic_configurator.store.get_case_by_internal_id = Mock(return_value=wgs_tumor_only_case)

    # WHEN building the CLI input
    cli_input: BalsamicConfigInput = balsamic_configurator._build_cli_input(
        case_id=wgs_tumor_only_case.internal_id
    )

    # THEN pydantic model should be created (and validated)
    assert isinstance(cli_input, BalsamicConfigInput)

    # THEN the correct normal sample name should be set
    assert cli_input.normal_sample_name == "normal_sample"

    # THEN the correct gens_coverage_pon should be chosen (Male)
    assert cli_input.gens_coverage_pon == balsamic_configurator.gens_coverage_male_path

    # THEN fields not relevant for WGS analyses should be set to their default values
    for field in PANEL_ONLY_FIELDS:
        assert getattr(cli_input, field) == BalsamicConfigInput.model_fields[field].default


def test_build_cli_input_panel_tumor_only(
    balsamic_configurator: BalsamicConfigurator, bed_version_short_name: str
):
    # GIVEN a case with one tumor panel sample
    panel_tumor_only_case = create_autospec(Case, data_analysis="balsamic", internal_id="case_1")
    application = create_autospec(Application, prep_category="tgs")
    application_version = create_autospec(ApplicationVersion, application=application)
    sample_1 = create_autospec(
        Sample,
        internal_id="sample1",
        is_tumour=True,
        application_version=application_version,
        sex=SexOptions.MALE,
    )
    panel_tumor_only_case.samples = [sample_1]
    balsamic_configurator.store.get_case_by_internal_id = Mock(return_value=panel_tumor_only_case)

    # GIVEN that LIMS returns a panel name that exists in the store
    balsamic_configurator.lims_api.capture_kit = Mock(return_value=bed_version_short_name)

    # GIVEN that there exists matching pon files
    balsamic_configurator._get_pon_file = Mock(return_value=Path("path/to/pon.cnn"))

    # WHEN building the CLI input
    cli_input: BalsamicConfigInput = balsamic_configurator._build_cli_input(
        case_id=panel_tumor_only_case.internal_id
    )

    # THEN a BalsamicConfigInput instance should be created (and validated)
    assert isinstance(cli_input, BalsamicConfigInput)

    # THEN the correct normal sample name should be set
    assert cli_input.normal_sample_name is None

    # THEN fields not relevant for panel analyses should be set to their default values
    for field in WGS_ONLY_FIELDS:
        assert getattr(cli_input, field) == BalsamicConfigInput.model_fields[field].default


def test_build_cli_input_panel_exome_only(
    balsamic_configurator: BalsamicConfigurator, bed_version_short_name: str
):
    # GIVEN a case with one exome sample
    exome_tumor_only_case = create_autospec(Case, data_analysis="balsamic", internal_id="case_1")
    application = create_autospec(Application, prep_category="wes")
    application_version = create_autospec(ApplicationVersion, application=application)
    sample_1 = create_autospec(
        Sample,
        internal_id="sample1",
        is_tumour=True,
        application_version=application_version,
        sex=SexOptions.MALE,
    )
    exome_tumor_only_case.samples = [sample_1]
    balsamic_configurator.store.get_case_by_internal_id = Mock(return_value=exome_tumor_only_case)

    # GIVEN that LIMS returns a panel name that exists in the store
    balsamic_configurator.lims_api.capture_kit = Mock(return_value=bed_version_short_name)

    # GIVEN that there exists matching pon files
    balsamic_configurator._get_pon_file = Mock(return_value=Path("path/to/pon.cnn"))

    # WHEN building the CLI input
    cli_input: BalsamicConfigInput = balsamic_configurator._build_cli_input(
        case_id=exome_tumor_only_case.internal_id
    )

    # THEN pydantic model should be created (and validated)
    assert isinstance(cli_input, BalsamicConfigInput)

    # THEN the correct normal sample name should be set
    assert cli_input.normal_sample_name is None

    # THEN fields not relevant for panel analyses should be set to their default values
    for field in WGS_ONLY_FIELDS:
        assert getattr(cli_input, field) == BalsamicConfigInput.model_fields[field].default

    # THEN the exome flag should be set to True
    assert cli_input.exome is True


def test_get_config(balsamic_configurator: BalsamicConfigurator, case_id: str, tmp_path: Path):
    """Tests that the get_config method returns a BalsamicCaseConfig. And that fields can be overridden with flags."""
    # GIVEN a Balsamic configurator with an existing config file
    balsamic_configurator.root_dir = tmp_path
    Path(balsamic_configurator.root_dir, case_id).mkdir()
    Path(balsamic_configurator.root_dir, case_id, f"{case_id}.json").touch()

    # GIVEN that the database returns a case with the provided case_id
    case_to_configure = create_autospec(Case, internal_id=case_id)
    case_to_configure.slurm_priority = SlurmQos.NORMAL
    balsamic_configurator.store.get_case_by_internal_id = Mock(return_value=case_to_configure)

    # WHEN getting the config
    config: BalsamicCaseConfig = balsamic_configurator.get_config(
        case_id=case_id, qos=SlurmQos.EXPRESS
    )

    # THEN the config should be a BalsamicCaseConfig
    assert isinstance(config, BalsamicCaseConfig)

    # THEN the qos should be set to the provided value
    assert config.qos == SlurmQos.EXPRESS


def test_get_config_missing_config_file(
    balsamic_configurator: BalsamicConfigurator, case_id: str, tmp_path: Path
):
    """Tests that the get_config method raises an error if the config file is missing."""
    # GIVEN a BalsamicConfigurator
    balsamic_configurator.root_dir = tmp_path

    # GIVEN that the config file does not exist

    # GIVEN that the database returns a case with the provided case_id
    case_to_configure = create_autospec(Case, internal_id=case_id)
    case_to_configure.slurm_priority = SlurmQos.NORMAL
    balsamic_configurator.store.get_case_by_internal_id = Mock(return_value=case_to_configure)

    # WHEN getting the config
    # THEN it should raise a CaseNotConfiguredError
    with pytest.raises(CaseNotConfiguredError):
        balsamic_configurator.get_config(case_id=case_id)
