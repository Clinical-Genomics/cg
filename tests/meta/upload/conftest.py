"""Fixtures for meta/upload tests."""

from datetime import datetime
from pathlib import Path

import pytest

from cg.apps.coverage.api import ChanjoAPI
from cg.apps.housekeeper.hk import HousekeeperAPI
from cg.constants import Workflow
from cg.constants.housekeeper_tags import HkMipAnalysisTag
from cg.meta.upload.coverage import UploadCoverageApi
from cg.meta.upload.gt import UploadGenotypesAPI
from cg.models.cg_config import CGConfig
from cg.store.models import Analysis, Case, Sample
from cg.store.store import Store

from tests.store_helpers import StoreHelpers


class MockCoverage(ChanjoAPI):
    """Mock chanjo coverage api."""


@pytest.fixture
def upload_genotypes_hk_bundle(
    case_id: str, timestamp, case_qc_metrics_deliverables: Path, bcf_file: Path
) -> dict:
    """Returns a dictionary in Housekeeper format with files used in upload Genotype process."""
    data = {
        "name": case_id,
        "created": timestamp,
        "expires": timestamp,
        "files": [
            {
                "path": str(case_qc_metrics_deliverables),
                "archive": False,
                "tags": HkMipAnalysisTag.QC_METRICS,
            },
            {"path": str(bcf_file), "archive": False, "tags": ["snv-gbcf", "genotype"]},
        ],
    }
    return data


@pytest.fixture
def analysis_obj(
    analysis_store_trio: Store, case_id: str, timestamp: datetime, helpers: StoreHelpers
) -> Analysis:
    """Return an analysis object with a trio."""
    case_obj = analysis_store_trio.get_case_by_internal_id(internal_id=case_id)
    helpers.add_analysis(store=analysis_store_trio, case=case_obj, started_at=timestamp)
    return analysis_store_trio.get_case_by_internal_id(internal_id=case_id).analyses[0]


@pytest.fixture
def upload_genotypes_api(
    real_housekeeper_api, genotype_api, upload_genotypes_hk_bundle, helpers: StoreHelpers
) -> UploadGenotypesAPI:
    """Create a upload genotypes api."""
    helpers.ensure_hk_bundle(real_housekeeper_api, upload_genotypes_hk_bundle, include=True)
    _api = UploadGenotypesAPI(
        hk_api=real_housekeeper_api,
        gt_api=genotype_api,
    )

    return _api


@pytest.fixture(scope="function")
def coverage_upload_api(
    chanjo_config: dict[str, dict[str, str]], populated_housekeeper_api: HousekeeperAPI
):
    """Return a upload coverage API."""
    return UploadCoverageApi(
        status_api=None, hk_api=populated_housekeeper_api, chanjo_api=MockCoverage(chanjo_config)
    )


@pytest.fixture(name="genotype_analysis_sex")
def genotype_analysis_sex() -> dict:
    """Return predicted sex per sample_id."""
    return {"ADM1": "male", "ADM2": "male", "ADM3": "female"}


@pytest.fixture(name="mip_dna_case")
def mip_dna_case(mip_dna_context: CGConfig, helpers: StoreHelpers) -> Case:
    """Return a MIP DNA case."""

    store: Store = mip_dna_context.status_db

    mip_dna_case: Case = helpers.add_case(
        store=store,
        internal_id="mip-dna-case",
        name="mip-dna-case",
        data_analysis=Workflow.MIP_DNA,
    )
    dna_mip_sample: Sample = helpers.add_sample(
        store=store, application_type="wgs", internal_id="mip-dna-case"
    )
    helpers.add_relationship(store=store, case=mip_dna_case, sample=dna_mip_sample)

    helpers.add_analysis(store=store, case=mip_dna_case, workflow=Workflow.MIP_DNA)

    return mip_dna_case


@pytest.fixture(name="mip_rna_case")
def mip_rna_case(mip_rna_context: CGConfig, case_id: str):
    """Return a MIP RNA case."""
    return mip_rna_context.status_db.get_case_by_internal_id(internal_id=case_id)


@pytest.fixture(name="mip_rna_analysis")
def mip_rna_analysis(mip_rna_context: CGConfig, helpers: StoreHelpers, mip_rna_case: Case) -> Case:
    """Return a MIP RNA analysis."""
    return helpers.add_analysis(
        store=mip_rna_context.status_db, case=mip_rna_case, workflow=Workflow.MIP_RNA
    )
