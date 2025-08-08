from pathlib import Path
from unittest.mock import Mock, create_autospec

import pytest
from pytest_mock import MockerFixture

from cg.apps.lims import LimsAPI
from cg.constants import GenePanelMasterList
from cg.constants.constants import DEFAULT_CAPTURE_KIT, StatusOptions
from cg.constants.tb import AnalysisType
from cg.exc import BedVersionNotFoundError, LimsDataError
from cg.models.orders.sample_base import SexEnum
from cg.services.analysis_starter.configurator.file_creators import mip_dna_config
from cg.services.analysis_starter.configurator.file_creators.mip_dna_config import (
    MIPDNAConfigFileCreator,
)
from cg.store.models import Application, ApplicationVersion, BedVersion, Case, CaseSample, Sample
from cg.store.store import Store


@pytest.fixture
def expected_content_wgs() -> dict:
    """Fixture to provide expected content for the MIP DNA config file."""
    return {
        "case": "case_id",
        "default_gene_panels": [GenePanelMasterList.OMIM_AUTO],
        "samples": [
            {
                "analysis_type": AnalysisType.WGS,
                "capture_kit": "default.bed",
                "expected_coverage": 26,
                "father": "0",
                "mother": "0",
                "phenotype": StatusOptions.UNAFFECTED,
                "sample_display_name": "sample_name",
                "sample_id": "sample_id",
                "sex": SexEnum.male,
            },
        ],
    }


@pytest.fixture
def expected_content_wes() -> dict:
    """Fixture to provide expected content for the MIP DNA config file."""
    return {
        "case": "case_id",
        "default_gene_panels": [GenePanelMasterList.OMIM_AUTO, GenePanelMasterList.PANELAPP_GREEN],
        "samples": [
            {
                "analysis_type": AnalysisType.WES,
                "capture_kit": "mock_bed_version.bed",
                "expected_coverage": 26,
                "father": "0",
                "mother": "mother_id",
                "phenotype": StatusOptions.AFFECTED,
                "sample_display_name": "sample_name",
                "sample_id": "sample_id",
                "sex": SexEnum.male,
            },
        ],
    }


@pytest.fixture
def case_id() -> str:
    return "case_id"


@pytest.fixture
def sample() -> Sample:
    application: Application = create_autospec(Application, min_sequencing_depth=26)
    application_version: ApplicationVersion = create_autospec(
        ApplicationVersion, application=application
    )
    sample = create_autospec(
        Sample,
        internal_id="sample_id",
        sex=SexEnum.male,
        prep_category=AnalysisType.WGS,
        application_version=application_version,
    )
    sample.name = "sample_name"
    return sample


@pytest.fixture
def case_sample(sample: Sample) -> CaseSample:
    return create_autospec(
        CaseSample, father=None, mother=None, sample=sample, status=StatusOptions.UNKNOWN
    )


@pytest.fixture
def wgs_mock_store(case_id: str, case_sample: CaseSample) -> Store:
    case: Case = create_autospec(
        Case, internal_id=case_id, links=[case_sample], panels=[GenePanelMasterList.OMIM_AUTO]
    )
    case_sample.case = case
    store: Store = create_autospec(Store)
    store.get_case_by_internal_id_strict = Mock(return_value=case)
    return store


def test_create_wgs_no_bed_flag(
    case_id: str, expected_content_wgs: dict, wgs_mock_store: Store, mocker: MockerFixture
):
    # GIVEN a mock store and a case id

    # GIVEN a config file creator
    file_creator = MIPDNAConfigFileCreator(lims_api=Mock(), root="root", store=wgs_mock_store)

    # GIVEN a patched writer
    mock_write = mocker.patch.object(mip_dna_config, "write_yaml")

    # WHEN creating a config file without a bed flag
    file_creator.create(case_id=case_id, bed_flag=None)

    # THEN the config file is created with the default capture kit
    expected_content_wgs["samples"][0]["capture_kit"] = DEFAULT_CAPTURE_KIT
    mock_write.assert_called_once_with(
        content=expected_content_wgs, file_path=Path("root", case_id, "pedigree.yaml")
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
    file_creator.create(case_id=case_id, bed_flag="bed_file.bed")

    # THEN the config file is created with the default capture kit
    expected_content_wgs["samples"][0]["capture_kit"] = "bed_file.bed"
    mock_write.assert_called_once_with(
        content=expected_content_wgs, file_path=Path("root", case_id, "pedigree.yaml")
    )


def test_create_wgs_bed_short_name_provided(
    case_id: str, expected_content_wgs: dict, wgs_mock_store: Store, mocker: MockerFixture
):
    # GIVEN a case id and a mock store that returns a valid bed version for a short name
    wgs_mock_store.get_bed_version_by_short_name_strict = Mock(
        return_value=create_autospec(BedVersion, filename="existing_bed_file.bed")
    )

    # GIVEN a config file creator
    file_creator = MIPDNAConfigFileCreator(lims_api=Mock(), root="root", store=wgs_mock_store)

    # GIVEN a patched writer
    mock_write = mocker.patch.object(mip_dna_config, "write_yaml")

    # WHEN creating a config file providing a bed file name
    file_creator.create(case_id=case_id, bed_flag="bed_short_name")

    # THEN the config file is created with the default capture kit
    expected_content_wgs["samples"][0]["capture_kit"] = "existing_bed_file.bed"
    mock_write.assert_called_once_with(
        content=expected_content_wgs, file_path=Path("root", case_id, "pedigree.yaml")
    )


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
    case_sample: CaseSample,
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
    case_sample.mother = mother
    case_sample.father = father

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
    config_file_creator.create(case_id=case_id, bed_flag="default.bed")

    # THEN the config file is created with mother and father set
    mock_write.assert_called_once_with(
        content=expected_content_wgs, file_path=Path("root", case_id, "pedigree.yaml")
    )


def test_create_wgs(expected_content_wgs: dict, mocker: MockerFixture):
    # GIVEN a mocked store
    application: Application = create_autospec(Application, min_sequencing_depth=26)
    application_version: ApplicationVersion = create_autospec(
        ApplicationVersion, application=application
    )
    sample = create_autospec(
        Sample,
        internal_id="sample_id",
        sex=SexEnum.male,
        prep_category=AnalysisType.WGS,
        application_version=application_version,
    )
    sample.name = "sample_name"
    mother = create_autospec(Sample, internal_id="mother_id")
    case_sample: CaseSample = create_autospec(
        CaseSample, father=None, mother=mother, sample=sample, status=StatusOptions.UNKNOWN
    )
    case_id = "case_id"
    case: Case = create_autospec(
        Case, internal_id=case_id, links=[case_sample], panels=[GenePanelMasterList.OMIM_AUTO]
    )
    case_sample.case = case

    store: Store = create_autospec(Store)
    store.get_case_by_internal_id_strict = Mock(return_value=case)

    # GIVEN a MIPDNAConfigFileCreator
    root = "mip_root"
    file_creator = MIPDNAConfigFileCreator(lims_api=Mock(), root=root, store=store)

    # GIVEN a patched writer
    mock_write = mocker.patch.object(mip_dna_config, "write_yaml")

    # WHEN creating the config file
    file_creator.create(case_id=case_id, bed_flag=None)

    # THEN the writer is called with the correct content and file path
    mock_write.assert_called_once_with(
        content=expected_content_wgs, file_path=Path(root, case_id, "pedigree.yaml")
    )


def test_wgs_fails_bed_name_not_in_store():
    # GIVEN a mock store
    store: Store = create_autospec(Store)
    store.get_bed_version_by_short_name_strict = Mock(side_effect=BedVersionNotFoundError)

    # GIVEN a config file creator
    file_creator = MIPDNAConfigFileCreator(lims_api=Mock(), root="", store=store)

    # WHEN creating the config file providing a bed short name that doesn't exist in the store
    # THEN a BedVersionNotFound error is raised
    with pytest.raises(BedVersionNotFoundError):
        file_creator.create(case_id="case_id", bed_flag="bed_file")


# TODO: Write test for downsampled sample


def test_create_wes(expected_content_wes: dict, mocker: MockerFixture):
    # GIVEN a mocked store
    application: Application = create_autospec(Application, min_sequencing_depth=26)
    application_version: ApplicationVersion = create_autospec(
        ApplicationVersion, application=application
    )
    sample = create_autospec(
        Sample,
        internal_id="sample_id",
        sex=SexEnum.male,
        prep_category=AnalysisType.WES,
        application_version=application_version,
        from_sample=None,
    )
    sample.name = "sample_name"
    mother = create_autospec(Sample, internal_id="mother_id")
    case_sample: CaseSample = create_autospec(
        CaseSample, father=None, mother=mother, sample=sample, status=StatusOptions.AFFECTED
    )
    case_id = "case_id"
    case: Case = create_autospec(
        Case,
        internal_id=case_id,
        links=[case_sample],
        panels=[GenePanelMasterList.OMIM_AUTO, GenePanelMasterList.PANELAPP_GREEN],
    )
    store: Store = create_autospec(Store)
    store.get_case_by_internal_id_strict = Mock(return_value=case)
    # TODO: Test the scenario when store returns None

    # GIVEN a BED verson in the store
    bed_version: BedVersion = create_autospec(BedVersion, filename="mock_bed_version.bed")
    store.get_bed_version_by_short_name_strict = Mock(return_value=bed_version)

    # GIVEN a LIMS mock
    lims: LimsAPI = create_autospec(LimsAPI)
    lims.get_capture_kit_strict = Mock(return_value="capture_kit_short_name")

    # GIVEN a MIPDNAConfigFileCreator
    root = "mip_root"
    file_creator = MIPDNAConfigFileCreator(lims_api=Mock(), root=root, store=store)

    # GIVEN a patched writer
    mock_write = mocker.patch.object(mip_dna_config, "write_yaml")

    # WHEN creating the config file when the provided bed flag is None
    file_creator.create(case_id=case_id, bed_flag=None)

    # THEN the writer is called with the correct content and file path
    mock_write.assert_called_once_with(
        content=expected_content_wes, file_path=Path(root, case_id, "pedigree.yaml")
    )


def test_create_config_wes_with_downsampled_sample():
    # GIVEN a mocked store
    application: Application = create_autospec(Application, min_sequencing_depth=26)
    application_version: ApplicationVersion = create_autospec(
        ApplicationVersion, application=application
    )
    sample = create_autospec(
        Sample,
        internal_id="sample_id",
        sex=SexEnum.male,
        prep_category=AnalysisType.WES,
        application_version=application_version,
        from_sample="other_sample_id",  # Is it really a string??
    )
    sample.name = "sample_name"
    mother = create_autospec(Sample, internal_id="mother_id")
    case_sample: CaseSample = create_autospec(
        CaseSample, father=None, mother=mother, sample=sample, status=StatusOptions.AFFECTED
    )
    case_id = "case_id"
    case: Case = create_autospec(
        Case,
        internal_id=case_id,
        links=[case_sample],
        panels=[GenePanelMasterList.OMIM_AUTO, GenePanelMasterList.PANELAPP_GREEN],
    )
    store: Store = create_autospec(Store)
    store.get_case_by_internal_id_strict = Mock(return_value=case)

    # GIVEN a BED verson in the store
    bed_version: BedVersion = create_autospec(BedVersion, filename="mock_bed_version.bed")
    store.get_bed_version_by_short_name_strict = Mock(return_value=bed_version)

    # GIVEN a LIMS mock
    lims: LimsAPI = create_autospec(LimsAPI)
    lims.get_capture_kit_strict = Mock(return_value="capture_kit_short_name")

    # GIVEN a MIPDNAConfigFileCreator
    root = "mip_root"
    file_creator = MIPDNAConfigFileCreator(lims_api=Mock(), root=root, store=store)


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
        file_creator.create(case_id=case_id, bed_flag=None)
