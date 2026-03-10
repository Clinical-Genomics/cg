from pathlib import Path
from subprocess import CalledProcessError, CompletedProcess
from unittest.mock import ANY, Mock, create_autospec

import pytest
from pytest_mock import MockerFixture

import cg.services.analysis_starter.configurator.file_creators.balsamic_config as creator
from cg.apps.lims.api import LimsAPI
from cg.constants import SexOptions
from cg.constants.constants import BedVersionGenomeVersion
from cg.constants.observations import BalsamicObservationPanel
from cg.constants.process import EXIT_SUCCESS
from cg.constants.sequencing import SeqLibraryPrepCategory
from cg.exc import CaseNotFoundError, LimsDataError
from cg.models.cg_config import BalsamicConfig
from cg.services.analysis_starter.configurator.file_creators.balsamic_config import (
    BalsamicConfigFileCreator,
    subprocess,
)
from cg.store.models import BedVersion, Case, Sample
from cg.store.store import Store


def test_create_tgs_myeloid_normal_only(
    cg_balsamic_config: BalsamicConfig,
    expected_tgs_myeloid_normal_only_command: str,
    mocker: MockerFixture,
):
    # GIVEN a store with a TGS normal-only case
    sample: Sample = create_autospec(
        Sample,
        internal_id="sample_normal",
        is_tumour=False,
        prep_category=SeqLibraryPrepCategory.TARGETED_GENOME_SEQUENCING,
        sex=SexOptions.FEMALE,
    )
    tgs_normal_only_case: Case = create_autospec(
        Case, data_analysis="balsamic", internal_id="case_1", samples=[sample]
    )
    store: Store = create_autospec(Store)
    store.get_case_by_internal_id_strict = Mock(return_value=tgs_normal_only_case)

    # GIVEN a bed version for a myeloid capture kit
    store.get_bed_version_by_short_name_and_genome_version_strict = Mock(
        return_value=create_autospec(
            BedVersion,
            bed_name=BalsamicObservationPanel.MYELOID,
            filename="myeloid.bed",
            shortname="myeloid_short_name",
        )
    )

    # GIVEN a Lims API with the myeloid capture kit
    lims_api: LimsAPI = create_autospec(LimsAPI)
    lims_api.get_capture_kit_strict = Mock(return_value="myeloid_short_name")

    # GIVEN a BalsamicConfigFileCreator
    config_file_creator = BalsamicConfigFileCreator(
        status_db=store, lims_api=lims_api, cg_balsamic_config=cg_balsamic_config
    )

    # GIVEN that the subprocess exits successfully
    mock_runner = mocker.patch.object(
        creator.subprocess, "run", return_value=CompletedProcess(args="", returncode=EXIT_SUCCESS)
    )

    # WHEN creating the config file
    config_file_creator.create(
        case_id="case_1", fastq_path=Path(f"{cg_balsamic_config.root}/case_1/fastq")
    )

    # THEN the expected command is called
    mock_runner.assert_called_once_with(
        args=expected_tgs_myeloid_normal_only_command, check=False, shell=True, stderr=-1, stdout=-1
    )

    # THEN the bed version should have been fetched using the LIMS capture kit
    store.get_bed_version_by_short_name_and_genome_version_strict.assert_called_once_with(
        short_name="myeloid_short_name", genome_version=BedVersionGenomeVersion.HG19
    )


def test_create_tgs_lymphoid_paired(
    cg_balsamic_config: BalsamicConfig,
    expected_tgs_lymphoid_paired_command: str,
    mocker: MockerFixture,
):
    # GIVEN a store with TGS paired case
    tumour_sample: Sample = create_autospec(
        Sample,
        internal_id="sample_tumour",
        is_tumour=True,
        sex=SexOptions.MALE,
        prep_category=SeqLibraryPrepCategory.TARGETED_GENOME_SEQUENCING,
    )
    normal_sample: Sample = create_autospec(
        Sample,
        internal_id="sample_normal",
        is_tumour=False,
        sex=SexOptions.MALE,
        prep_category=SeqLibraryPrepCategory.TARGETED_GENOME_SEQUENCING,
    )
    tgs_paired_case: Case = create_autospec(
        Case, data_analysis="balsamic", internal_id="case_1", samples=[tumour_sample, normal_sample]
    )
    store: Store = create_autospec(Store)
    store.get_case_by_internal_id_strict = Mock(return_value=tgs_paired_case)

    # GIVEN a bed version for a lymphoid capture kit
    store.get_bed_version_by_short_name_and_genome_version_strict = Mock(
        return_value=create_autospec(
            BedVersion,
            bed_name=BalsamicObservationPanel.LYMPHOID,
            filename="lymphoid.bed",
            shortname="lymphoid_short_name",
        )
    )

    # GIVEN a Lims API with the lymphoid capture kit
    lims_api: LimsAPI = create_autospec(LimsAPI)
    lims_api.get_capture_kit_strict = Mock(return_value="lymphoid_short_name")

    # GIVEN a BalsamicConfigFileCreator
    config_file_creator = BalsamicConfigFileCreator(
        status_db=store, lims_api=lims_api, cg_balsamic_config=cg_balsamic_config
    )

    # GIVEN that the subprocess exits successfully
    mock_runner = mocker.patch.object(
        creator.subprocess, "run", return_value=CompletedProcess(args="", returncode=EXIT_SUCCESS)
    )

    # WHEN creating the config file
    config_file_creator.create(
        case_id="case_1", fastq_path=Path(f"{cg_balsamic_config.root}/case_1/fastq")
    )

    # THEN the expected command is called
    mock_runner.assert_called_once_with(
        args=expected_tgs_lymphoid_paired_command, check=False, shell=True, stderr=-1, stdout=-1
    )

    # THEN the bed version should have been fetched using the LIMS capture kit
    store.get_bed_version_by_short_name_and_genome_version_strict.assert_called_once_with(
        short_name="lymphoid_short_name",
        genome_version=BedVersionGenomeVersion.HG19,
    )


def test_create_tgs_tumour_only(
    cg_balsamic_config: BalsamicConfig, expected_tgs_tumour_only_command: str, mocker: MockerFixture
):
    # GIVEN a store with a TGS tumor-only case
    tumour_sample: Sample = create_autospec(
        Sample,
        internal_id="sample_tumour",
        is_tumour=True,
        sex=SexOptions.UNKNOWN,
        prep_category=SeqLibraryPrepCategory.TARGETED_GENOME_SEQUENCING,
    )
    tgs_tumour_only_case: Case = create_autospec(
        Case, data_analysis="balsamic", internal_id="case_1", samples=[tumour_sample]
    )
    store: Store = create_autospec(Store)
    store.get_case_by_internal_id_strict = Mock(return_value=tgs_tumour_only_case)

    # GIVEN a bed version without a LoqusDB dump file nor PON file
    store.get_bed_version_by_short_name_and_genome_version_strict = Mock(
        return_value=create_autospec(
            BedVersion,
            bed_name="bed_without_a_dump_file",
            filename="bed_version.bed",
            shortname="bed_short_name",
        )
    )

    # GIVEN a Lims API with a capture kit that has no LoqusDB dump file nor PON file
    lims_api: LimsAPI = create_autospec(LimsAPI)
    lims_api.get_capture_kit_strict = Mock(return_value="bed_short_name")

    # GIVEN a BalsamicConfigFileCreator
    config_file_creator = BalsamicConfigFileCreator(
        status_db=store, lims_api=lims_api, cg_balsamic_config=cg_balsamic_config
    )

    # GIVEN that the subprocess exits successfully
    mock_runner = mocker.patch.object(
        creator.subprocess, "run", return_value=CompletedProcess(args="", returncode=EXIT_SUCCESS)
    )

    # WHEN creating the config file
    config_file_creator.create(
        case_id="case_1", fastq_path=Path(f"{cg_balsamic_config.root}/case_1/fastq")
    )

    # THEN the expected command is called
    mock_runner.assert_called_once_with(
        args=expected_tgs_tumour_only_command, check=False, shell=True, stderr=-1, stdout=-1
    )

    # THEN the bed version should have been fetched using the LIMS capture kit
    store.get_bed_version_by_short_name_and_genome_version_strict.assert_called_once_with(
        short_name="bed_short_name",
        genome_version=BedVersionGenomeVersion.HG19,
    )


def test_create_override_panel_bed(
    cg_balsamic_config: BalsamicConfig, expected_tgs_tumour_only_command: str, mocker: MockerFixture
):
    # GIVEN a store with a TGS tumor-only case
    tumour_sample: Sample = create_autospec(
        Sample,
        internal_id="sample_tumour",
        is_tumour=True,
        sex=SexOptions.UNKNOWN,
        prep_category=SeqLibraryPrepCategory.TARGETED_GENOME_SEQUENCING,
    )
    tgs_tumour_only_case: Case = create_autospec(
        Case, data_analysis="balsamic", internal_id="case_1", samples=[tumour_sample]
    )
    store: Store = create_autospec(Store)
    store.get_case_by_internal_id_strict = Mock(return_value=tgs_tumour_only_case)
    store.get_bed_version_by_short_name_and_genome_version_strict = Mock(
        return_value=create_autospec(BedVersion, filename="bed_version.bed")
    )

    # GIVEN a BalsamicConfigFileCreator
    config_file_creator = BalsamicConfigFileCreator(
        status_db=store, lims_api=Mock(), cg_balsamic_config=cg_balsamic_config
    )

    # GIVEN that the subprocess exits successfully
    mock_runner = mocker.patch.object(
        creator.subprocess, "run", return_value=CompletedProcess(args="", returncode=EXIT_SUCCESS)
    )

    # WHEN creating the config file providing a panel bed
    config_file_creator.create(
        case_id="case_1",
        fastq_path=Path(f"{cg_balsamic_config.root}/case_1/fastq"),
        panel_bed="override_panel_bed",
    )

    # THEN the expected command is called
    mock_runner.assert_called_once_with(
        args=expected_tgs_tumour_only_command, check=False, shell=True, stderr=-1, stdout=-1
    )

    # THEN the panel bed flag value is used
    store.get_bed_version_by_short_name_and_genome_version_strict.assert_called_once_with(
        short_name="override_panel_bed",
        genome_version=BedVersionGenomeVersion.HG19,
    )


def test_create_wes_normal_only(
    cg_balsamic_config: BalsamicConfig, expected_wes_normal_only_command: str, mocker: MockerFixture
):
    # GIVEN a case with one normal WES sample
    sample: Sample = create_autospec(
        Sample,
        internal_id="sample_normal",
        is_tumour=False,
        prep_category=SeqLibraryPrepCategory.WHOLE_EXOME_SEQUENCING,
        sex=SexOptions.FEMALE,
    )
    wes_normal_only_case: Case = create_autospec(
        Case, data_analysis="balsamic", internal_id="case_1", samples=[sample]
    )
    store: Store = create_autospec(Store)
    store.get_case_by_internal_id_strict = Mock(return_value=wes_normal_only_case)

    # GIVEN a bed version for the exome capture kit
    store.get_bed_version_by_short_name_and_genome_version_strict = Mock(
        return_value=create_autospec(
            BedVersion,
            bed_name=BalsamicObservationPanel.EXOME,
            filename="exome.bed",
            shortname="exome_short_name",
        )
    )

    # GIVEN a Lims API
    lims_api: LimsAPI = create_autospec(LimsAPI)
    lims_api.get_capture_kit_strict = Mock(return_value="exome_short_name")

    # GIVEN a BalsamicConfigFileCreator
    config_file_creator = BalsamicConfigFileCreator(
        status_db=store, lims_api=lims_api, cg_balsamic_config=cg_balsamic_config
    )

    # GIVEN that the subprocess exits successfully
    mock_runner = mocker.patch.object(
        creator.subprocess, "run", return_value=CompletedProcess(args="", returncode=EXIT_SUCCESS)
    )

    # WHEN creating the config file
    config_file_creator.create(
        case_id="case_1", fastq_path=Path(f"{cg_balsamic_config.root}/case_1/fastq")
    )

    # THEN the expected command is called
    mock_runner.assert_called_once_with(
        args=expected_wes_normal_only_command, check=False, shell=True, stderr=-1, stdout=-1
    )

    # THEN the bed version should have been fetched using the LIMS capture kit
    store.get_bed_version_by_short_name_and_genome_version_strict.assert_called_once_with(
        short_name="exome_short_name",
        genome_version=BedVersionGenomeVersion.HG19,
    )


def test_create_wes_paired(
    cg_balsamic_config: BalsamicConfig, expected_wes_paired_command: str, mocker: MockerFixture
):
    # GIVEN a store with a WES paired case
    tumour_sample: Sample = create_autospec(
        Sample,
        internal_id="sample_tumour",
        is_tumour=True,
        sex=SexOptions.FEMALE,
        prep_category=SeqLibraryPrepCategory.WHOLE_EXOME_SEQUENCING,
    )
    normal_sample: Sample = create_autospec(
        Sample,
        internal_id="sample_normal",
        is_tumour=False,
        sex=SexOptions.FEMALE,
        prep_category=SeqLibraryPrepCategory.WHOLE_EXOME_SEQUENCING,
    )
    wes_paired_case: Case = create_autospec(
        Case, data_analysis="balsamic", internal_id="case_1", samples=[tumour_sample, normal_sample]
    )
    store: Store = create_autospec(Store)
    store.get_case_by_internal_id_strict = Mock(return_value=wes_paired_case)

    # GIVEN a bed version for the exome capture kit
    store.get_bed_version_by_short_name_and_genome_version_strict = Mock(
        return_value=create_autospec(
            BedVersion,
            bed_name=BalsamicObservationPanel.EXOME,
            filename="exome.bed",
            shortname="exome_short_name",
        )
    )

    # GIVEN a Lims API
    lims_api: LimsAPI = create_autospec(LimsAPI)
    lims_api.get_capture_kit_strict = Mock(return_value="twist_exome")

    # GIVEN a BalsamicConfigFileCreator
    config_file_creator = BalsamicConfigFileCreator(
        status_db=store, lims_api=lims_api, cg_balsamic_config=cg_balsamic_config
    )

    # GIVEN that the subprocess exits successfully
    mock_runner = mocker.patch.object(
        creator.subprocess, "run", return_value=CompletedProcess(args="", returncode=EXIT_SUCCESS)
    )

    # WHEN creating the config file
    config_file_creator.create(
        case_id="case_1", fastq_path=Path(f"{cg_balsamic_config.root}/case_1/fastq")
    )

    # THEN the expected command is called
    mock_runner.assert_called_once_with(
        args=expected_wes_paired_command, check=False, shell=True, stderr=-1, stdout=-1
    )

    # THEN the bed version should have been fetched using the LIMS capture kit
    store.get_bed_version_by_short_name_and_genome_version_strict.assert_called_once_with(
        short_name="twist_exome",
        genome_version=BedVersionGenomeVersion.HG19,
    )


def test_create_wes_tumour_only(
    cg_balsamic_config: BalsamicConfig, expected_wes_tumour_only_command: str, mocker: MockerFixture
):
    # GIVEN a case with one tumor WES sample
    sample: Sample = create_autospec(
        Sample,
        internal_id="sample_1",
        is_tumour=True,
        prep_category=SeqLibraryPrepCategory.WHOLE_EXOME_SEQUENCING,
        sex=SexOptions.FEMALE,
    )
    wes_tumor_only_case: Case = create_autospec(
        Case, data_analysis="balsamic", internal_id="case_1", samples=[sample]
    )
    store: Store = create_autospec(Store)
    store.get_case_by_internal_id_strict = Mock(return_value=wes_tumor_only_case)

    # GIVEN a bed version for the exome capture kit
    store.get_bed_version_by_short_name_and_genome_version_strict = Mock(
        return_value=create_autospec(
            BedVersion,
            bed_name=BalsamicObservationPanel.EXOME,
            filename="exome.bed",
            shortname="exome_short_name",
        )
    )

    # GIVEN a Lims API
    lims_api: LimsAPI = create_autospec(LimsAPI)
    lims_api.get_capture_kit_strict = Mock(return_value="exome_short_name")

    # GIVEN a BalsamicConfigFileCreator
    config_file_creator = BalsamicConfigFileCreator(
        status_db=store, lims_api=lims_api, cg_balsamic_config=cg_balsamic_config
    )

    # GIVEN that the subprocess exits successfully
    mock_runner = mocker.patch.object(
        creator.subprocess, "run", return_value=CompletedProcess(args="", returncode=EXIT_SUCCESS)
    )

    # WHEN creating the config file
    config_file_creator.create(
        case_id="case_1", fastq_path=Path(f"{cg_balsamic_config.root}/case_1/fastq")
    )

    # THEN the expected command is called
    mock_runner.assert_called_once_with(
        args=expected_wes_tumour_only_command, check=False, shell=True, stderr=-1, stdout=-1
    )

    # THEN the bed version should have been fetched using the LIMS capture kit
    store.get_bed_version_by_short_name_and_genome_version_strict.assert_called_once_with(
        short_name="exome_short_name",
        genome_version=BedVersionGenomeVersion.HG19,
    )


def test_create_wgs_paired(
    cg_balsamic_config: BalsamicConfig, expected_wgs_paired_command: str, mocker: MockerFixture
):
    # GIVEN a store with a WGS paired case
    tumour_sample: Sample = create_autospec(
        Sample,
        internal_id="sample_tumour",
        is_tumour=True,
        sex=SexOptions.FEMALE,
        prep_category=SeqLibraryPrepCategory.WHOLE_GENOME_SEQUENCING,
    )
    normal_sample: Sample = create_autospec(
        Sample,
        internal_id="sample_normal",
        is_tumour=False,
        sex=SexOptions.FEMALE,
        prep_category=SeqLibraryPrepCategory.WHOLE_GENOME_SEQUENCING,
    )
    wgs_paired_case: Case = create_autospec(
        Case, data_analysis="balsamic", internal_id="case_1", samples=[tumour_sample, normal_sample]
    )
    store: Store = create_autospec(Store)
    store.get_case_by_internal_id_strict = Mock(return_value=wgs_paired_case)

    # GIVEN a BalsamicConfigFileCreator
    config_file_creator = BalsamicConfigFileCreator(
        status_db=store, lims_api=Mock(), cg_balsamic_config=cg_balsamic_config
    )

    # GIVEN that the subprocess exits successfully
    mock_runner = mocker.patch.object(
        creator.subprocess, "run", return_value=CompletedProcess(args="", returncode=EXIT_SUCCESS)
    )

    # WHEN creating the config file
    config_file_creator.create(
        case_id="case_1", fastq_path=Path(f"{cg_balsamic_config.root}/case_1/fastq")
    )

    # THEN the expected command is called
    mock_runner.assert_called_once_with(
        args=expected_wgs_paired_command, check=False, shell=True, stderr=-1, stdout=-1
    )


def test_create_wgs_tumor_only(
    cg_balsamic_config: BalsamicConfig, expected_wgs_tumour_only_command: str, mocker: MockerFixture
):
    # GIVEN a store with a WGS tumor-only case
    sample: Sample = create_autospec(
        Sample,
        internal_id="sample_1",
        is_tumour=True,
        prep_category=SeqLibraryPrepCategory.WHOLE_GENOME_SEQUENCING,
        sex=SexOptions.MALE,
    )
    wgs_tumor_only_case: Case = create_autospec(
        Case, data_analysis="balsamic", internal_id="case_1", samples=[sample]
    )
    store: Store = create_autospec(Store)
    store.get_case_by_internal_id_strict = Mock(return_value=wgs_tumor_only_case)

    # GIVEN a BalsamicConfigFileCreator
    config_file_creator = BalsamicConfigFileCreator(
        status_db=store, lims_api=Mock(), cg_balsamic_config=cg_balsamic_config
    )

    # GIVEN that the subprocess exits successfully
    mock_runner = mocker.patch.object(
        creator.subprocess, "run", return_value=CompletedProcess(args="", returncode=EXIT_SUCCESS)
    )

    # WHEN creating the config file
    config_file_creator.create(
        case_id="case_1", fastq_path=Path(f"{cg_balsamic_config.root}/case_1/fastq")
    )

    # THEN the expected command is called
    mock_runner.assert_called_once_with(
        args=expected_wgs_tumour_only_command, check=False, shell=True, stderr=-1, stdout=-1
    )


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
        config_file_creator.create(case_id="non_existing_case", fastq_path=Path("/some/path"))


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
    store.get_bed_version_by_short_name_and_genome_version_strict = Mock(
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
        config_file_creator.create(
            case_id="case_1", fastq_path=Path(f"{cg_balsamic_config.root}/case_1/fastq")
        )


def test_balsamic_config_case_command_fails(
    cg_balsamic_config: BalsamicConfig, mocker: MockerFixture
):
    # GIVEN a store with a Balsamic case
    sample: Sample = create_autospec(
        Sample,
        internal_id="sample_1",
        is_tumour=True,
        prep_category=SeqLibraryPrepCategory.WHOLE_GENOME_SEQUENCING,
        sex=SexOptions.MALE,
    )
    wgs_tumor_only_case: Case = create_autospec(
        Case, data_analysis="balsamic", internal_id="case_1", samples=[sample]
    )
    store: Store = create_autospec(Store)
    store.get_case_by_internal_id_strict = Mock(return_value=wgs_tumor_only_case)

    # GIVEN a BalsamicConfigFileCreator
    config_file_creator = BalsamicConfigFileCreator(
        status_db=store, lims_api=Mock(), cg_balsamic_config=cg_balsamic_config
    )

    # GIVEN that the Balsamic config case command fails
    mock_run = mocker.patch.object(
        subprocess, "run", side_effect=CalledProcessError(returncode=2, cmd="config case")
    )

    # WHEN creating the config file for the case
    # THEN a CalledProcessError is raised
    with pytest.raises(CalledProcessError):
        config_file_creator.create(
            case_id="case_1", fastq_path=Path(f"{cg_balsamic_config.root}/case_1/fastq")
        )

    # THEN the run was called with check=False
    mock_run.assert_called_once_with(args=ANY, shell=ANY, check=False, stdout=ANY, stderr=ANY)


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
