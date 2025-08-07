from pathlib import Path
from unittest.mock import Mock, create_autospec

import pytest
from pytest_mock import MockerFixture

from cg.apps.lims import LimsAPI
from cg.constants import GenePanelMasterList
from cg.constants.constants import DEFAULT_CAPTURE_KIT, StatusOptions
from cg.constants.tb import AnalysisType
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
                "capture_kit": DEFAULT_CAPTURE_KIT,
                "expected_coverage": 26,
                "father": "0",
                "mother": "mother_id",
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
    file_creator = MIPDNAConfigFileCreator(lims_api=Mock(), store=store)

    # GIVEN a patched writer
    mock_write = mocker.patch.object(mip_dna_config, "write_yaml")

    # WHEN creating the config file
    file_creator.create(case_id=case_id, bed_flag=None)

    # THEN the writer is called with the correct content and file path
    mock_write.assert_called_once_with(
        content=expected_content_wgs, file_path=Path(root, case_id, "pedigree.yaml")
    )


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
    # TODO: Test the scenario when lims returns None
    lims.capture_kit = Mock(return_value="capture_kit_short_name")

    # GIVEN a MIPDNAConfigFileCreator
    file_creator = MIPDNAConfigFileCreator(lims_api=Mock(), store=store)

    # GIVEN a patched writer
    mock_write = mocker.patch.object(mip_dna_config, "write_yaml")

    # WHEN creating the config file
    file_creator.create(case_id=case_id, bed_flag=None)

    # THEN the writer is called with the correct content and file path
    mock_write.assert_called_once_with(content=expected_content_wes, file_path=Path("."))
