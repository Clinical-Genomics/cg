from pathlib import Path
from unittest.mock import Mock, create_autospec

import pytest
from pytest_mock import MockerFixture

from cg.apps.lims import LimsAPI
from cg.constants.constants import DEFAULT_CAPTURE_KIT, StatusOptions
from cg.constants.tb import AnalysisType
from cg.exc import BedVersionNotFoundError, LimsDataError
from cg.services.analysis_starter.configurator.file_creators import mip_dna_config
from cg.services.analysis_starter.configurator.file_creators.mip_dna_config import (
    MIPDNAConfigFileCreator,
)
from cg.store.models import BedVersion, Case, CaseSample, Sample
from cg.store.store import Store


def test_create_wgs_no_bed_flag(
    case_id: str, expected_content_wgs: dict, wgs_mock_store: Store, mocker: MockerFixture
):
    # GIVEN a mock store and a case id

    # GIVEN a config file creator
    file_creator = MIPDNAConfigFileCreator(lims_api=Mock(), root="root", store=wgs_mock_store)

    # GIVEN a patched writer
    mock_write = mocker.patch.object(mip_dna_config, "write_yaml")

    # WHEN creating a config file without a bed flag
    file_creator.create(case_id=case_id, bed_flag=None, file_path=Path("pedigree.yaml"))

    # THEN the config file is created with the default capture kit
    expected_content_wgs["samples"][0]["capture_kit"] = DEFAULT_CAPTURE_KIT
    mock_write.assert_called_once_with(
        content=expected_content_wgs, file_path=Path("pedigree.yaml")
    )


def test_create_wgs_bed_file_provided(
    case_id: str, expected_content_wgs: dict, wgs_mock_store: Store, mocker: MockerFixture
):
    # GIVEN a mock store and a case id

    # GIVEN a config file creator
    file_creator = MIPDNAConfigFileCreator(lims_api=Mock(), root="root", store=wgs_mock_store)

    # GIVEN a patched writer
    mock_write = mocker.patch.object(mip_dna_config, "write_yaml")

    # WHEN creating a config file providing a bed file name
    file_creator.create(case_id=case_id, bed_flag="bed_file.bed", file_path=Path("pedigree.yaml"))

    # THEN the config file is created with the default capture kit
    expected_content_wgs["samples"][0]["capture_kit"] = "bed_file.bed"
    mock_write.assert_called_once_with(
        content=expected_content_wgs, file_path=Path("pedigree.yaml")
    )


def test_create_wgs_bed_short_name_provided(
    case_id: str, expected_content_wgs: dict, wgs_mock_store: Store, mocker: MockerFixture
):
    # GIVEN a case id and a mock store that returns a valid bed version for a short name
    wgs_mock_store.get_bed_version_by_short_name_and_genome_version_strict = Mock(
        return_value=create_autospec(BedVersion, filename="existing_bed_file.bed")
    )

    # GIVEN a config file creator
    file_creator = MIPDNAConfigFileCreator(lims_api=Mock(), root="root", store=wgs_mock_store)

    # GIVEN a patched writer
    mock_write = mocker.patch.object(mip_dna_config, "write_yaml")

    # WHEN creating a config file providing a bed file name
    file_creator.create(case_id=case_id, bed_flag="bed_short_name", file_path=Path("pedigree.yaml"))

    # THEN the config file is created with the default capture kit
    expected_content_wgs["samples"][0]["capture_kit"] = "existing_bed_file.bed"
    mock_write.assert_called_once_with(
        content=expected_content_wgs, file_path=Path("pedigree.yaml")
    )


def test_wgs_fails_bed_name_not_in_store():
    # GIVEN a mock store
    store: Store = create_autospec(Store)
    store.get_bed_version_by_short_name_and_genome_version_strict = Mock(
        side_effect=BedVersionNotFoundError
    )

    # GIVEN a config file creator
    file_creator = MIPDNAConfigFileCreator(lims_api=Mock(), root="", store=store)

    # WHEN creating the config file providing a bed short name that doesn't exist in the store
    # THEN a BedVersionNotFound error is raised
    with pytest.raises(BedVersionNotFoundError):
        file_creator.create(case_id="case_id", bed_flag="bed_file", file_path=Path("pedigree.yaml"))


@pytest.mark.parametrize(
    "mother, expected_mother_field",
    [(None, "0"), (create_autospec(Sample, internal_id="mother_sample"), "mother_sample")],
    ids=["no mother", "mother set"],
)
@pytest.mark.parametrize(
    "father, expected_father_field",
    [(None, "0"), (create_autospec(Sample, internal_id="father_sample"), "father_sample")],
    ids=["no father", "father set"],
)
def test_create_wgs_father_and_mother_set(
    case_id: str,
    wgs_case_sample: CaseSample,
    expected_father_field: str,
    expected_mother_field: str,
    expected_content_wgs: dict,
    father: Sample | None,
    mother: Sample | None,
    wgs_mock_store: Store,
    mocker: MockerFixture,
):
    # GIVEN a mock store and a case id

    # GIVEN a mother and father is set on the case sample
    wgs_case_sample.mother = mother
    wgs_case_sample.father = father

    # GIVEN a file content that have an expected mother and father
    expected_content_wgs["samples"][0]["mother"] = expected_mother_field
    expected_content_wgs["samples"][0]["father"] = expected_father_field

    # GIVEN a config file creator
    config_file_creator = MIPDNAConfigFileCreator(
        lims_api=Mock(), root="root", store=wgs_mock_store
    )

    # GIVEN a patched writer
    mock_write = mocker.patch.object(mip_dna_config, "write_yaml")

    # WHEN creating a config file providing a bed file name
    config_file_creator.create(
        case_id=case_id, bed_flag="default.bed", file_path=Path("pedigree.yaml")
    )

    # THEN the config file is created with mother and father set
    mock_write.assert_called_once_with(
        content=expected_content_wgs, file_path=Path("pedigree.yaml")
    )


def test_create_wgs_only_one_sample_phenotype_unknown(
    case_id: str,
    expected_content_wgs: dict,
    wgs_case_sample: CaseSample,
    wgs_mock_store: Store,
    mocker: MockerFixture,
):
    # GIVEN a case with a single case sample with status unknown
    wgs_case_sample.status = StatusOptions.UNKNOWN

    # GIVEN a store

    # GIVEN a config file creator
    file_creator = MIPDNAConfigFileCreator(lims_api=Mock(), root="root", store=wgs_mock_store)

    # GIVEN a mocked writer
    mock_write = mocker.patch.object(mip_dna_config, "write_yaml")

    # WHEN creating the config file
    file_creator.create(case_id=case_id, bed_flag="default.bed", file_path=Path("pedigree.yaml"))

    # THEN the phenotype should have been set to unaffected
    expected_content_wgs["samples"][0]["phenotype"] = StatusOptions.UNAFFECTED
    mock_write.assert_called_once_with(
        content=expected_content_wgs, file_path=Path("pedigree.yaml")
    )

    # THEN the type of the phenotype value should be str
    # (not StrEnum since they don't serialize properly when using write_yaml)
    assert type(mock_write.call_args.kwargs["content"]["samples"][0]["phenotype"]) is str


def test_create_wes_no_bed_flag(
    case_id: str, expected_content_wes: dict, wes_mock_store: Store, mocker: MockerFixture
):
    # GIVEN a LIMS mock
    lims: LimsAPI = create_autospec(LimsAPI)
    lims.get_capture_kit_strict = Mock(return_value="capture_kit_short_name")

    # GIVEN a MIPDNAConfigFileCreator
    root = "mip_root"
    file_creator = MIPDNAConfigFileCreator(lims_api=Mock(), root=root, store=wes_mock_store)

    # GIVEN a patched writer
    mock_write = mocker.patch.object(mip_dna_config, "write_yaml")

    # WHEN creating the config file when the provided bed flag is None
    file_creator.create(case_id=case_id, bed_flag=None, file_path=Path("pedigree.yaml"))

    # THEN the writer is called with the correct content and file path
    mock_write.assert_called_once_with(
        content=expected_content_wes, file_path=Path("pedigree.yaml")
    )


def test_create_config_wes_with_downsampled_sample(
    case_id: str, wes_mock_store: Store, wes_sample: Sample, mocker: MockerFixture
):
    # GIVEN that the sample is downsampled
    original_sample_id = "other_sample_id"
    wes_sample.from_sample = original_sample_id

    # GIVEN a LIMS mock
    lims: LimsAPI = create_autospec(LimsAPI)
    lims.get_capture_kit_strict = Mock(return_value="capture_kit_short_name")

    # GIVEN a patched writer
    mocker.patch.object(mip_dna_config, "write_yaml")

    # GIVEN a MIPDNAConfigFileCreator
    root = "mip_root"
    file_creator = MIPDNAConfigFileCreator(lims_api=lims, root=root, store=wes_mock_store)

    # WHEN creating the config file
    file_creator.create(case_id=case_id, bed_flag=None, file_path=Path("pedigree.yaml"))

    # THEN
    lims.get_capture_kit_strict.assert_called_once_with(original_sample_id)


def test_create_config_wes_lims_fails():
    lims_api: LimsAPI = create_autospec(LimsAPI)
    lims_api.get_capture_kit_strict = Mock(side_effect=LimsDataError)

    # GIVEN a mock store containing a case with a WES sample
    sample = create_autospec(
        Sample,
        internal_id="sample_id",
        prep_category=AnalysisType.WES,
        from_sample=None,
    )
    sample.name = "sample_name"
    case_sample: CaseSample = create_autospec(CaseSample, sample=sample)
    case_id = "case_id"
    case: Case = create_autospec(
        Case,
        internal_id=case_id,
        links=[case_sample],
    )
    store: Store = create_autospec(Store)
    store.get_case_by_internal_id_strict = Mock(return_value=case)

    # GIVEN a MIPDNAConfigFileCreator
    file_creator = MIPDNAConfigFileCreator(lims_api=lims_api, root="", store=store)

    # WHEN creating the config file when the provided bed flag is None

    # THEN a LimsDataError should be raised
    with pytest.raises(LimsDataError):
        file_creator.create(case_id=case_id, bed_flag=None, file_path=Path("pedigree.yaml"))
