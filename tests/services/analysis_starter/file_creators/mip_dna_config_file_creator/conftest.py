from unittest.mock import Mock, create_autospec

import pytest

from cg.constants.constants import StatusOptions
from cg.constants.gene_panel import GenePanelMasterList
from cg.constants.tb import AnalysisType
from cg.models.orders.sample_base import SexEnum
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
def wgs_sample() -> Sample:
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
def wgs_case_sample(wgs_sample: Sample) -> CaseSample:
    return create_autospec(
        CaseSample, father=None, mother=None, sample=wgs_sample, status=StatusOptions.AFFECTED
    )


@pytest.fixture
def wgs_mock_store(case_id: str, wgs_case_sample: CaseSample) -> Store:
    case: Case = create_autospec(
        Case, internal_id=case_id, links=[wgs_case_sample], panels=[GenePanelMasterList.OMIM_AUTO]
    )
    wgs_case_sample.case = case
    store: Store = create_autospec(Store)
    store.get_case_by_internal_id_strict = Mock(return_value=case)
    return store


@pytest.fixture
def wes_sample() -> Sample:
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
    return sample


@pytest.fixture
def wes_mock_store(case_id: str, wes_sample: Sample) -> Store:
    mother = create_autospec(Sample, internal_id="mother_id")
    case_sample: CaseSample = create_autospec(
        CaseSample, father=None, mother=mother, sample=wes_sample, status=StatusOptions.AFFECTED
    )
    case: Case = create_autospec(
        Case,
        internal_id=case_id,
        links=[case_sample],
        panels=[GenePanelMasterList.OMIM_AUTO, GenePanelMasterList.PANELAPP_GREEN],
        samples=[wes_sample],
    )
    case_sample.case = case
    store: Store = create_autospec(Store)
    store.get_case_by_internal_id_strict = Mock(return_value=case)

    bed_version: BedVersion = create_autospec(BedVersion, filename="mock_bed_version.bed")
    store.get_bed_version_by_short_name_strict = Mock(return_value=bed_version)
    return store
