"""Fixtures for the upload scout api tests"""

import json
import logging
from datetime import datetime
from pathlib import Path
from typing import List

import pytest
from housekeeper.store import models as hk_models

from cg.apps.scout.scout_load_config import ScoutIndividual, ScoutLoadConfig
from cg.meta.upload.scout.files import MipFileHandler, ScoutFileHandler
from cg.meta.upload.scout.hk_tags import TagInfo
from cg.meta.upload.scout.scoutapi import UploadScoutAPI

# Mocks
from tests.mocks.madeline import MockMadelineAPI
from tests.mocks.scout import MockScoutAPI

LOG = logging.getLogger(__name__)


class MockAnalysis:
    """Mock an analysis object"""

    @staticmethod
    def get_latest_metadata(family_id=None):
        """Mock get_latest_metadata"""
        # Returns: dict: parsed data
        # Define output dict
        outdata = {
            "analysis_sex": {"ADM1": "female", "ADM2": "female", "ADM3": "female"},
            "family": family_id or "yellowhog",
            "duplicates": {"ADM1": 13.525, "ADM2": 12.525, "ADM3": 14.525},
            "genome_build": "hg19",
            "rank_model_version": "1.18",
            "mapped_reads": {"ADM1": 98.8, "ADM2": 99.8, "ADM3": 97.8},
            "mip_version": "v4.0.20",
            "sample_ids": ["2018-20203", "2018-20204"],
            "sv_rank_model_version": "1.08",
        }
        return outdata

    @staticmethod
    def convert_panels(customer_id, panels):
        """Mock convert_panels"""
        _ = customer_id, panels
        return ""


class MockLims:
    """ Mock Lims API """

    lims = None

    def __init__(self, samples):
        self.lims = self
        self._samples = samples

    def sample(self, sample_id):
        """ Returns a lims sample matching the provided sample_id """
        for sample in self._samples:
            if sample["id"] == sample_id:
                return sample
        return None


@pytest.fixture(name="lims_family")
def fixture_lims_family() -> dict:
    """ Returns a lims-like family of samples """
    return json.load(open("tests/fixtures/report/lims_family.json"))


@pytest.fixture(name="lims_samples")
def fixture_lims_samples(lims_family: dict) -> List[dict]:
    """ Returns the samples of a lims family """
    return lims_family["samples"]


@pytest.fixture(name="upload_genotypes_hk_bundle")
def fixture_upload_genotypes_hk_bundle(
    case_id: str, timestamp: datetime, case_qc_metrics: Path, bcf_file: Path
) -> dict:
    """ Returns a dictionary in hk format with files used in upload gt process"""
    data = {
        "name": case_id,
        "created": timestamp,
        "expires": timestamp,
        "files": [
            {"path": str(case_qc_metrics), "archive": False, "tags": ["qcmetrics"]},
            {"path": str(bcf_file), "archive": False, "tags": ["snv-gbcf"]},
        ],
    }
    return data


@pytest.fixture(name="mip_file_handler")
def fixture_mip_file_handler(hk_version_obj: hk_models.Version) -> MipFileHandler:
    return MipFileHandler(hk_version_obj=hk_version_obj)


@pytest.yield_fixture(scope="function")
def upload_scout_api(
    scout_api: MockScoutAPI, madeline_api: MockMadelineAPI, lims_samples, populated_housekeeper_api
):
    """Fixture for upload_scout_api"""
    analysis_mock = MockAnalysis()
    lims_api = MockLims(lims_samples)

    _api = UploadScoutAPI(
        hk_api=populated_housekeeper_api,
        scout_api=scout_api,
        madeline_api=madeline_api,
        analysis_api=analysis_mock,
        lims_api=lims_api,
    )

    yield _api
