from pathlib import Path
from unittest.mock import Mock, create_autospec

import pytest
from pytest_mock import MockerFixture

import cg.services.analysis_starter.configurator.file_creators.balsamic_config as creator
from cg.apps.lims.api import LimsAPI
from cg.constants import SexOptions
from cg.constants.sequencing import SeqLibraryPrepCategory
from cg.exc import CaseNotFoundError, LimsDataError
from cg.models.cg_config import BalsamicConfig
from cg.services.analysis_starter.configurator.file_creators.balsamic_config import (
    BalsamicConfigFileCreator,
)
from cg.store.models import BedVersion, Case, Sample
from cg.store.store import Store


@pytest.mark.parametrize(
    "prep_category, expected_command_normal_only",
    [
        (SeqLibraryPrepCategory.TARGETED_GENOME_SEQUENCING, "expected_tgs_normal_only_command"),
        (SeqLibraryPrepCategory.WHOLE_EXOME_SEQUENCING, "expected_wes_normal_only_command"),
    ],
    ids=["tgs", "wes"],
)
def test_create_normal_only(
    cg_balsamic_config: BalsamicConfig,
    expected_command_normal_only,
    prep_category: SeqLibraryPrepCategory,
    mocker: MockerFixture,
    request: pytest.FixtureRequest,
):
    # GIVEN a case with one normal sample
    sample: Sample = create_autospec(
        Sample,
        internal_id="sample_normal",
        is_tumour=False,
        prep_category=prep_category,
        sex=SexOptions.FEMALE,
    )
    normal_only_case: Case = create_autospec(
        Case, data_analysis="balsamic", internal_id="case_1", samples=[sample]
    )

    store: Store = create_autospec(Store)
    store.get_case_by_internal_id_strict = Mock(return_value=normal_only_case)
    store.get_bed_version_by_short_name_strict = Mock(
        return_value=create_autospec(BedVersion, filename="bed_version.bed")
    )

    # GIVEN a Lims API
    lims_api: LimsAPI = create_autospec(LimsAPI)
    lims_api.get_capture_kit_strict = Mock(return_value="bed_short_name")

    # GIVEN a BalsamicConfigFileCreator
    config_file_creator = BalsamicConfigFileCreator(
        status_db=store, lims_api=lims_api, cg_balsamic_config=cg_balsamic_config
    )

    # GIVEN that the subprocess exits successfully
    mock_runner = mocker.patch.object(creator.subprocess, "run")

    # WHEN creating the config file
    config_file_creator.create(case_id="case_1")

    # THEN the expected command is called
    expected_command_normal_only: str = request.getfixturevalue(expected_command_normal_only)
    mock_runner.assert_called_once_with(
        args=expected_command_normal_only, check=True, shell=True, stderr=-1, stdout=-1
    )


@pytest.mark.parametrize(
    "prep_category, expected_command_paired",
    [
        (SeqLibraryPrepCategory.TARGETED_GENOME_SEQUENCING, "expected_tgs_paired_command"),
        (SeqLibraryPrepCategory.WHOLE_EXOME_SEQUENCING, "expected_wes_paired_command"),
        (SeqLibraryPrepCategory.WHOLE_GENOME_SEQUENCING, "expected_wgs_paired_command"),
    ],
    ids=["tgs", "wes", "wgs"],
)
def test_create_paired(
    cg_balsamic_config: BalsamicConfig,
    expected_command_paired,
    prep_category: SeqLibraryPrepCategory,
    mocker: MockerFixture,
    request: pytest.FixtureRequest,
):
    # GIVEN a case with one tumor and one normal samples
    tumour_sample: Sample = create_autospec(
        Sample,
        internal_id="sample_tumour",
        is_tumour=True,
        sex=SexOptions.FEMALE,
        prep_category=prep_category,
    )
    normal_sample: Sample = create_autospec(
        Sample,
        internal_id="sample_normal",
        is_tumour=False,
        sex=SexOptions.FEMALE,
        prep_category=prep_category,
    )
    paired_case: Case = create_autospec(
        Case, data_analysis="balsamic", internal_id="case_1", samples=[tumour_sample, normal_sample]
    )
    store: Store = create_autospec(Store)
    store.get_case_by_internal_id_strict = Mock(return_value=paired_case)
    store.get_bed_version_by_short_name_strict = Mock(
        return_value=create_autospec(BedVersion, filename="bed_version.bed")
    )

    # GIVEN a Lims API
    lims_api: LimsAPI = create_autospec(LimsAPI)
    lims_api.get_capture_kit_strict = Mock(return_value="bed_short_name")

    # GIVEN a BalsamicConfigFileCreator
    config_file_creator = BalsamicConfigFileCreator(
        status_db=store, lims_api=lims_api, cg_balsamic_config=cg_balsamic_config
    )

    # GIVEN that the subprocess exits successfully
    mock_runner = mocker.patch.object(creator.subprocess, "run")

    # WHEN creating the config file
    config_file_creator.create(case_id="case_1")

    # THEN the expected command is called
    expected_command_paired: str = request.getfixturevalue(expected_command_paired)
    mock_runner.assert_called_once_with(
        args=expected_command_paired, check=True, shell=True, stderr=-1, stdout=-1
    )


@pytest.mark.parametrize(
    "prep_category, expected_command_tumour_only",
    [
        (SeqLibraryPrepCategory.TARGETED_GENOME_SEQUENCING, "expected_tgs_tumour_only_command"),
        (SeqLibraryPrepCategory.WHOLE_EXOME_SEQUENCING, "expected_wes_tumour_only_command"),
        (SeqLibraryPrepCategory.WHOLE_GENOME_SEQUENCING, "expected_wgs_tumour_only_command"),
    ],
    ids=["tgs", "wes", "wgs"],
)
def test_create_tumour_only(
    cg_balsamic_config: BalsamicConfig,
    expected_command_tumour_only,
    prep_category: SeqLibraryPrepCategory,
    mocker: MockerFixture,
    request: pytest.FixtureRequest,
):
    # GIVEN a case with one tumor samples
    tumour_sample: Sample = create_autospec(
        Sample,
        internal_id="sample_tumour",
        is_tumour=True,
        sex=SexOptions.FEMALE,
        prep_category=prep_category,
    )
    tumour_only_case: Case = create_autospec(
        Case, data_analysis="balsamic", internal_id="case_1", samples=[tumour_sample]
    )
    store: Store = create_autospec(Store)
    store.get_case_by_internal_id_strict = Mock(return_value=tumour_only_case)
    store.get_bed_version_by_short_name_strict = Mock(
        return_value=create_autospec(BedVersion, filename="bed_version.bed")
    )

    # GIVEN a Lims API
    lims_api: LimsAPI = create_autospec(LimsAPI)
    lims_api.get_capture_kit_strict = Mock(return_value="bed_short_name")

    # GIVEN a BalsamicConfigFileCreator
    config_file_creator = BalsamicConfigFileCreator(
        status_db=store, lims_api=lims_api, cg_balsamic_config=cg_balsamic_config
    )

    # GIVEN that the subprocess exits successfully
    mock_runner = mocker.patch.object(creator.subprocess, "run")

    # WHEN creating the config file
    config_file_creator.create(case_id="case_1")

    # THEN the expected command is called
    expected_command_tumour_only: str = request.getfixturevalue(expected_command_tumour_only)
    mock_runner.assert_called_once_with(
        args=expected_command_tumour_only, check=True, shell=True, stderr=-1, stdout=-1
    )


def test_create_override_panel_bed(
    cg_balsamic_config: BalsamicConfig, expected_tgs_tumour_only_command, mocker: MockerFixture
):
    # GIVEN a case with one tumor TGS samples
    tumour_sample: Sample = create_autospec(
        Sample,
        internal_id="sample_tumour",
        is_tumour=True,
        sex=SexOptions.FEMALE,
        prep_category=SeqLibraryPrepCategory.TARGETED_GENOME_SEQUENCING,
    )
    tgs_tumour_only_case: Case = create_autospec(
        Case, data_analysis="balsamic", internal_id="case_1", samples=[tumour_sample]
    )
    store: Store = create_autospec(Store)
    store.get_case_by_internal_id_strict = Mock(return_value=tgs_tumour_only_case)
    store.get_bed_version_by_short_name_strict = Mock(
        return_value=create_autospec(BedVersion, filename="bed_version.bed")
    )

    # GIVEN a BalsamicConfigFileCreator
    config_file_creator = BalsamicConfigFileCreator(
        status_db=store, lims_api=Mock(), cg_balsamic_config=cg_balsamic_config
    )

    # GIVEN that the subprocess exits successfully
    mock_runner = mocker.patch.object(creator.subprocess, "run")

    # WHEN creating the config file
    config_file_creator.create(case_id="case_1", panel_bed="bed-short-name")

    # THEN the expected command is called
    mock_runner.assert_called_once_with(
        args=expected_tgs_tumour_only_command, check=True, shell=True, stderr=-1, stdout=-1
    )

    # THEN the panel bed flag value is used
    store.get_bed_version_by_short_name_strict.assert_called_once_with("bed-short-name")


def test_create_no_case_found(cg_balsamic_config: BalsamicConfig):
    # GIVEN a store without cases
    store: Store = create_autospec(Store)
    store.get_case_by_internal_id_strict = Mock(return_value=None, side_effect=CaseNotFoundError)

    # GIVEN a BalsamicConfigFileCreator
    config_file_creator = BalsamicConfigFileCreator(
        status_db=store, lims_api=Mock(), cg_balsamic_config=cg_balsamic_config
    )

    # WHEN creating a config file for a non-existing case
    # THEN a CaseNotFoundError is raised
    with pytest.raises(CaseNotFoundError):
        config_file_creator.create(case_id="non_existing_case")


def test_create_no_capture_kit_in_lims(cg_balsamic_config: BalsamicConfig):
    # GIVEN a store with a TGS Balsamic case
    tumour_sample: Sample = create_autospec(
        Sample,
        internal_id="sample_tumour",
        is_tumour=True,
        sex=SexOptions.FEMALE,
        prep_category=SeqLibraryPrepCategory.TARGETED_GENOME_SEQUENCING,
    )
    case_without_capture_kit: Case = create_autospec(
        Case, data_analysis="balsamic", internal_id="case_1", samples=[tumour_sample]
    )
    store: Store = create_autospec(Store)
    store.get_case_by_internal_id_strict = Mock(return_value=case_without_capture_kit)
    store.get_bed_version_by_short_name_strict = Mock(
        return_value=create_autospec(BedVersion, filename="bed_version.bed")
    )

    # GIVEN a LIMS API without a capture kit for the given case
    lims_api: LimsAPI = create_autospec(LimsAPI)
    lims_api.get_capture_kit_strict = Mock(side_effect=LimsDataError)

    # GIVEN a BalsamicConfigFileCreator
    config_file_creator = BalsamicConfigFileCreator(
        status_db=store, lims_api=lims_api, cg_balsamic_config=cg_balsamic_config
    )

    # WHEN creating the config file for the case
    # THEN a LimsDataError error is raised
    with pytest.raises(LimsDataError):
        config_file_creator.create(case_id="case_1")


def test_get_pon_file(cg_balsamic_config: BalsamicConfig, tmp_path: Path):
    # GIVEN a BalsamicConfigFileCreator
    config_file_creator = BalsamicConfigFileCreator(
        status_db=create_autospec(Store), lims_api=Mock(), cg_balsamic_config=cg_balsamic_config
    )
    config_file_creator.pon_directory = tmp_path

    # GIVEN a bed file
    panel_name = "GMS_duck"
    bed_file = Path(config_file_creator.bed_directory, f"{panel_name}.bed")

    # GIVEN two matching PON files
    old_pon_path = Path(tmp_path, f"{panel_name}_CNVkit_PON_reference_v1.cnn")
    new_pon_path = Path(tmp_path, f"{panel_name}_CNVkit_PON_reference_v2.cnn")
    for pon_path in [old_pon_path, new_pon_path]:
        pon_path.touch()

    # WHEN getting the pon path
    pon_path: Path | None = config_file_creator._get_pon_file(bed_file)

    # THEN the returned path should be the latest version
    assert pon_path == new_pon_path


def test_get_pon_file_no_files(cg_balsamic_config: BalsamicConfig, tmp_path: Path):
    # GIVEN a BalsamicConfigFileCreator
    config_file_creator = BalsamicConfigFileCreator(
        status_db=create_autospec(Store), lims_api=Mock(), cg_balsamic_config=cg_balsamic_config
    )
    config_file_creator.pon_directory = tmp_path

    # GIVEN a bed file with no matching PON files
    panel_name = "GMS_duck"
    bed_file = Path(config_file_creator.bed_directory, f"{panel_name}.bed")

    # WHEN getting the pon path
    pon_file: Path | None = config_file_creator._get_pon_file(bed_file)

    # THEN None should be returned
    assert pon_file is None


def test_get_pon_file_no_matching_files(cg_balsamic_config: BalsamicConfig, tmp_path: Path):
    """Test that None is returned when no matching PON files are found."""
    # GIVEN a BalsamicConfigFileCreator
    config_file_creator = BalsamicConfigFileCreator(
        status_db=create_autospec(Store), lims_api=Mock(), cg_balsamic_config=cg_balsamic_config
    )
    config_file_creator.pon_directory = tmp_path

    # GIVEN a bed file with no matching PON files
    panel_name = "GMS_duck"
    bed_file = Path(config_file_creator.bed_directory, f"{panel_name}.bed")

    # GIVEN that there are files in the directory but none match the expected pattern
    (tmp_path / "some_other_file.txt").touch()

    # WHEN getting the pon path
    pon_file: Path | None = config_file_creator._get_pon_file(bed_file)

    # THEN None should be returned
    assert pon_file is None


@pytest.mark.parametrize(
    "sex, expected_file",
    [
        (SexOptions.FEMALE, "coverage_female.txt"),
        (SexOptions.MALE, "coverage_male.txt"),
        (SexOptions.UNKNOWN, "coverage_female.txt"),
    ],
    ids=["female", "male", "unknown"],
)
def test_get_gens_coverage_pon(
    cg_balsamic_config: BalsamicConfig, sex: SexOptions, expected_file: str
):
    # GIVEN a BalsamicConfigFileCreator
    config_file_creator = BalsamicConfigFileCreator(
        status_db=Mock(), lims_api=Mock(), cg_balsamic_config=cg_balsamic_config
    )

    # WHEN getting the gens coverage file
    gens_pon_file: Path = config_file_creator._get_gens_coverage_pon_file(sex)

    # THEN the file is the expected
    assert gens_pon_file.name == expected_file
