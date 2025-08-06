from pathlib import Path
from unittest.mock import Mock, create_autospec

import pytest
from pytest_mock import MockerFixture

from cg.constants.constants import DEFAULT_CAPTURE_KIT, StatusOptions
from cg.constants.tb import AnalysisType
from cg.models.orders.sample_base import SexEnum
from cg.services.analysis_starter.configurator.file_creators import mip_dna_config
from cg.services.analysis_starter.configurator.file_creators.mip_dna_config import (
    MIPDNAConfigFileCreator,
)
from cg.store.models import Application, ApplicationVersion, Case, CaseSample, Sample
from cg.store.store import Store


@pytest.fixture
def expected_content_wgs() -> dict:
    """Fixture to provide expected content for the MIP DNA config file."""
    return {
        "case": "case_id",
        "default_gene_panels": [],
        "samples": [
            {
                "analysis_type": AnalysisType.WGS,
                "capture_kit": DEFAULT_CAPTURE_KIT,
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
def expected_content_wes() -> dict:
    """Fixture to provide expected content for the MIP DNA config file."""
    return {
        "case": "case_id",
        "default_gene_panels": [],
        "samples": [
            {
                "analysis_type": AnalysisType.WES,
                "capture_kit": "",
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
        CaseSample, father=None, mother=mother, sample=sample, status=StatusOptions.AFFECTED
    )
    case_id = "case_id"
    case: Case = create_autospec(Case, internal_id=case_id, links=[case_sample])
    store: Store = create_autospec(Store)
    store.get_case_by_internal_id_strict = Mock(return_value=case)

    # GIVEN a MIPDNAConfigFileCreator
    file_creator = MIPDNAConfigFileCreator(lims_api=Mock(), store=store)

    # GIVEN a patched writer
    mock_write = mocker.patch.object(mip_dna_config, "write_yaml")

    # WHEN creating the config file
    file_creator.create(case_id=case_id, bed_flag=None)

    # THEN the writer is called with the correct content and file path
    mock_write.assert_called_once_with(content=expected_content_wgs, file_path=Path("."))


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
    )
    sample.name = "sample_name"
    mother = create_autospec(Sample, internal_id="mother_id")
    case_sample: CaseSample = create_autospec(
        CaseSample, father=None, mother=mother, sample=sample, status=StatusOptions.AFFECTED
    )
    case_id = "case_id"
    case: Case = create_autospec(Case, internal_id=case_id, links=[case_sample])
    store: Store = create_autospec(Store)
    store.get_case_by_internal_id_strict = Mock(return_value=case)

    # GIVEN a MIPDNAConfigFileCreator
    file_creator = MIPDNAConfigFileCreator(lims_api=Mock(), store=store)

    # GIVEN a patched writer
    mock_write = mocker.patch.object(mip_dna_config, "write_yaml")

    # WHEN creating the config file
    file_creator.create(case_id=case_id, bed_flag=None)

    # THEN the writer is called with the correct content and file path
    mock_write.assert_called_once_with(content=expected_content_wes, file_path=Path("."))
