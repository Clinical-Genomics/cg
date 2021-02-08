"""Fixtures for the upload scout api tests"""

import json
import logging
from datetime import datetime
from pathlib import Path
from typing import List

import pytest
from cg.constants import Pipeline
from cg.meta.upload.scout.balsamic_config_builder import BalsamicConfigBuilder
from cg.meta.upload.scout.mip_config_builder import MipConfigBuilder
from cg.meta.upload.scout.scout_load_config import MipLoadConfig
from cg.meta.upload.scout.scoutapi import UploadScoutAPI
from cg.store import Store, models
from housekeeper.store import models as hk_models

# Mocks
from tests.mocks.hk_mock import MockHousekeeperAPI
from tests.mocks.limsmock import MockLimsAPI
from tests.mocks.madeline import MockMadelineAPI
from tests.mocks.scout import MockScoutAPI
from tests.store_helpers import StoreHelpers

LOG = logging.getLogger(__name__)


class MockAnalysis:
    """Mock an analysis object"""

    @staticmethod
    def get_latest_metadata(family_id=None):
        """Mock get_latest_metadata"""
        # Returns: dict: parsed data
        # Define output dict
        out_data = {
            "analysis_sex": {"ADM1": "female", "ADM2": "female", "ADM3": "female"},
            "case": family_id or "yellowhog",
            "duplicates": {"ADM1": 13.525, "ADM2": 12.525, "ADM3": 14.525},
            "genome_build": "hg19",
            "rank_model_version": "1.18",
            "mapped_reads": {"ADM1": 98.8, "ADM2": 99.8, "ADM3": 97.8},
            "mip_version": "v4.0.20",
            "sample_ids": ["2018-20203", "2018-20204"],
            "sv_rank_model_version": "1.08",
        }
        return out_data

    @staticmethod
    def convert_panels(customer_id, panels):
        """Mock convert_panels"""
        _ = customer_id, panels
        return ""


@pytest.fixture(name="lims_family")
def fixture_lims_family() -> dict:
    """ Returns a lims-like case of samples """
    return json.load(open("tests/fixtures/report/lims_family.json"))


@pytest.fixture(name="lims_samples")
def fixture_lims_samples(lims_family: dict) -> List[dict]:
    """ Returns the samples of a lims case """
    return lims_family["samples"]


@pytest.fixture(scope="function", name="mip_analysis_hk_bundle_data")
def fixture_mip_analysis_hk_bundle_data(
    case_id: str, timestamp: datetime, mip_dna_analysis_dir: Path, sample_id: str
) -> dict:
    """Get some bundle data for housekeeper"""
    data = {
        "name": case_id,
        "created": timestamp,
        "expires": timestamp,
        "files": [
            {
                "path": str(mip_dna_analysis_dir / "snv.vcf"),
                "archive": False,
                "tags": ["vcf-snv-clinical"],
            },
            {
                "path": str(mip_dna_analysis_dir / "sv.vcf"),
                "archive": False,
                "tags": ["vcf-sv-clinical"],
            },
            {
                "path": str(mip_dna_analysis_dir / "snv_research.vcf"),
                "archive": False,
                "tags": ["vcf-snv-research"],
            },
            {
                "path": str(mip_dna_analysis_dir / "sv_research.vcf"),
                "archive": False,
                "tags": ["vcf-sv-research"],
            },
            {
                "path": str(mip_dna_analysis_dir / "str.vcf"),
                "archive": False,
                "tags": ["vcf-str"],
            },
            {
                "path": str(mip_dna_analysis_dir / "smn.vcf"),
                "archive": False,
                "tags": ["smn-calling"],
            },
            {
                "path": str(mip_dna_analysis_dir / "adm1.cram"),
                "archive": False,
                "tags": ["cram", sample_id],
            },
            {
                "path": str(mip_dna_analysis_dir / "report.pdf"),
                "archive": False,
                "tags": ["delivery-report"],
            },
            {
                "path": str(mip_dna_analysis_dir / "adm1.mt.bam"),
                "archive": False,
                "tags": ["bam-mt", sample_id],
            },
            {
                "path": str(mip_dna_analysis_dir / "vcf2cytosure.txt"),
                "archive": False,
                "tags": ["vcf2cytosure", sample_id],
            },
            {
                "path": str(mip_dna_analysis_dir / "multiqc.html"),
                "archive": False,
                "tags": ["multiqc-html", sample_id],
            },
        ],
    }
    return data


@pytest.fixture(scope="function", name="balsamic_analysis_hk_bundle_data")
def fixture_balsamic_analysis_hk_bundle_data(
    case_id: str, timestamp: datetime, balsamic_panel_analysis_dir: Path, sample_id: str
) -> dict:
    """Get some bundle data for housekeeper"""
    data = {
        "name": case_id,
        "created": timestamp,
        "expires": timestamp,
        "files": [
            {
                "path": str(balsamic_panel_analysis_dir / "snv.vcf"),
                "archive": False,
                "tags": ["vcf-snv-clinical"],
            },
            {
                "path": str(balsamic_panel_analysis_dir / "sv.vcf"),
                "archive": False,
                "tags": ["vcf-sv-clinical"],
            },
            {
                "path": str(balsamic_panel_analysis_dir / "adm1.cram"),
                "archive": False,
                "tags": ["cram", sample_id],
            },
        ],
    }
    return data


@pytest.fixture(name="balsamic_analysis_hk_version")
def fixture_balsamic_analysis_hk_version(
    housekeeper_api: MockHousekeeperAPI, balsamic_analysis_hk_bundle_data: dict, helpers
) -> MockHousekeeperAPI:
    return helpers.ensure_hk_version(housekeeper_api, balsamic_analysis_hk_bundle_data)


@pytest.fixture(name="mip_analysis_hk_version")
def fixture_mip_analysis_hk_version(
    housekeeper_api: MockHousekeeperAPI, mip_analysis_hk_bundle_data: dict, helpers
) -> MockHousekeeperAPI:
    return helpers.ensure_hk_version(housekeeper_api, mip_analysis_hk_bundle_data)


@pytest.fixture(name="mip_analysis_hk_api")
def fixture_mip_analysis_hk_api(
    housekeeper_api: MockHousekeeperAPI, mip_analysis_hk_bundle_data: dict, helpers
) -> MockHousekeeperAPI:
    """Return a housekeeper api populated with some mip analysis files"""
    helpers.ensure_hk_version(housekeeper_api, mip_analysis_hk_bundle_data)
    return housekeeper_api


@pytest.fixture(name="balsamic_analysis_hk_api")
def fixture_balsamic_analysis_hk_api(
    housekeeper_api: MockHousekeeperAPI, balsamic_analysis_hk_bundle_data: dict, helpers
) -> MockHousekeeperAPI:
    """Return a housekeeper api populated with some mip analysis files"""
    helpers.ensure_hk_version(housekeeper_api, balsamic_analysis_hk_bundle_data)
    return housekeeper_api


@pytest.fixture(name="mip_file_handler")
def fixture_mip_file_handler(mip_analysis_hk_version: hk_models.Version) -> MipConfigBuilder:
    return MipConfigBuilder(hk_version_obj=mip_analysis_hk_version)


@pytest.fixture(name="mip_analysis_obj")
def fixture_mip_analysis_obj(
    analysis_store_trio: Store, case_id: str, timestamp: datetime, helpers: StoreHelpers
) -> models.Analysis:
    case_obj: models.Family = analysis_store_trio.family(case_id)
    analysis_obj: models.Analysis = helpers.add_analysis(
        store=analysis_store_trio,
        case=case_obj,
        started_at=timestamp,
        pipeline=Pipeline.MIP_DNA,
        completed_at=timestamp,
    )
    return analysis_obj


@pytest.fixture(name="balsamic_analysis_obj")
def fixture_balsamic_analysis_obj(analysis_obj: models.Analysis) -> models.Analysis:
    for link_object in analysis_obj.family.links:
        link_object.sample.application_version.application.prep_category = "wes"
    return analysis_obj


@pytest.fixture(name="mip_config_builder")
def fixture_mip_config_builder(
    mip_analysis_hk_version: hk_models.Version,
    mip_analysis_obj: models.Analysis,
    lims_api: MockLimsAPI,
    mip_analysis_api: MockAnalysis,
    madeline_api: MockMadelineAPI,
) -> MipConfigBuilder:
    return MipConfigBuilder(
        hk_version_obj=mip_analysis_hk_version,
        analysis_obj=mip_analysis_obj,
        lims_api=lims_api,
        mip_analysis_api=mip_analysis_api,
        madeline_api=madeline_api,
    )


@pytest.fixture(name="balsamic_config_builder")
def fixture_balsamic_config_builder(
    balsamic_analysis_hk_version: hk_models.Version,
    balsamic_analysis_obj: models.Analysis,
    lims_api: MockLimsAPI,
) -> BalsamicConfigBuilder:
    return BalsamicConfigBuilder(
        hk_version_obj=balsamic_analysis_hk_version,
        analysis_obj=balsamic_analysis_obj,
        lims_api=lims_api,
    )


@pytest.fixture(name="mip_load_config")
def fixture_mip_load_config(
    mip_dna_analysis_dir: Path, case_id: str, customer_id: str
) -> MipLoadConfig:
    """Return a valid mip load_config"""
    return MipLoadConfig(
        owner=customer_id,
        family=case_id,
        vcf_snv=str(mip_dna_analysis_dir / "snv.vcf"),
        track="rare",
    )


@pytest.fixture(name="lims_api")
def fixture_lims_api(lims_samples: List[dict]) -> MockLimsAPI:
    return MockLimsAPI(samples=lims_samples)


@pytest.fixture(name="mip_analysis_api")
def fixture_mip_analysis_api() -> MockAnalysis:
    return MockAnalysis()


@pytest.fixture(name="upload_scout_api")
def fixture_upload_scout_api(
    scout_api: MockScoutAPI,
    madeline_api: MockMadelineAPI,
    lims_samples: List[dict],
    housekeeper_api: MockHousekeeperAPI,
) -> UploadScoutAPI:
    """Fixture for upload_scout_api"""
    analysis_mock = MockAnalysis()
    lims_api = MockLimsAPI(samples=lims_samples)

    return UploadScoutAPI(
        hk_api=housekeeper_api,
        scout_api=scout_api,
        madeline_api=madeline_api,
        analysis_api=analysis_mock,
        lims_api=lims_api,
    )


@pytest.yield_fixture(name="upload_mip_analysis_scout_api")
def fixture_upload_mip_analysis_scout_api(
    scout_api: MockScoutAPI,
    madeline_api: MockMadelineAPI,
    lims_samples: List[dict],
    mip_analysis_hk_api: MockHousekeeperAPI,
) -> UploadScoutAPI:
    """Fixture for upload_scout_api"""
    analysis_mock = MockAnalysis()
    lims_api = MockLimsAPI(samples=lims_samples)

    _api = UploadScoutAPI(
        hk_api=mip_analysis_hk_api,
        scout_api=scout_api,
        madeline_api=madeline_api,
        analysis_api=analysis_mock,
        lims_api=lims_api,
    )

    yield _api


@pytest.yield_fixture(name="upload_balsamic_analysis_scout_api")
def fixture_upload_balsamic_analysis_scout_api(
    scout_api: MockScoutAPI,
    madeline_api: MockMadelineAPI,
    lims_samples: List[dict],
    balsamic_analysis_hk_api: MockHousekeeperAPI,
) -> UploadScoutAPI:
    """Fixture for upload_scout_api"""
    analysis_mock = MockAnalysis()
    lims_api = MockLimsAPI(samples=lims_samples)

    _api = UploadScoutAPI(
        hk_api=balsamic_analysis_hk_api,
        scout_api=scout_api,
        madeline_api=madeline_api,
        analysis_api=analysis_mock,
        lims_api=lims_api,
    )

    yield _api
