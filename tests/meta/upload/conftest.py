"""Fixtures for meta/upload tests"""

import json

from pathlib import Path
from datetime import datetime

import pytest

from cg.apps.coverage.api import ChanjoAPI
from cg.constants import Pipeline
from cg.meta.upload.coverage import UploadCoverageApi
from cg.meta.upload.mutacc import UploadToMutaccAPI
from cg.meta.upload.observations import UploadObservationsAPI
from cg.meta.upload.scoutapi import UploadScoutAPI
from cg.meta.upload.gt import UploadGenotypesAPI
from cg.store import models
from cg.store import Store


# Mocks


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


class MockCoverage(ChanjoAPI):
    """Mock chanjo coverage api"""


class MockMutaccAuto:
    """ Mock class for mutacc_auto api """

    @staticmethod
    def extract_reads(*args, **kwargs):
        """mock extract_reads method"""
        _, _ = args, kwargs

    @staticmethod
    def import_reads(*args, **kwargs):
        """ mock import_reads method """
        _, _ = args, kwargs


class MockScoutApi:
    """Mock class for Scout api"""

    @staticmethod
    def get_causative_variants(case_id):
        """mock get_causative_variants"""
        _ = case_id
        return []

    @property
    def client(self):
        """Client URI"""
        return "mongodb://"

    @property
    def name(self):
        """Name property"""
        return self._name

    @name.setter
    def name(self, value):
        self._name = value

    @name.deleter
    def name(self):
        del self._name


class MockLoqusAPI:
    """ Mock LoqusAPI class"""

    def __init__(self, analysis_type="wgs"):
        self.analysis_type = analysis_type

    @staticmethod
    def load(*args, **kwargs):
        """ Mock load method"""
        _ = args
        _ = kwargs
        return dict(variants=12)

    @staticmethod
    def get_case(*args, **kwargs):
        """ Mock get_case method"""
        _ = args
        _ = kwargs
        return {"case_id": "case_id", "_id": "123"}

    @staticmethod
    def get_duplicate(*args, **kwargs):
        """Mock get_duplicate method"""
        _ = args
        _ = kwargs
        return {"case_id": "case_id"}


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
def fixture_lims_family():
    """ Returns a lims-like family of samples """
    return json.load(open("tests/fixtures/report/lims_family.json"))


@pytest.fixture(name="lims_samples")
def fixture_lims_samples(lims_family):
    """ Returns the samples of a lims family """
    return lims_family["samples"]


@pytest.fixture(name="upload_genotypes_hk_bundle")
def fixture_upload_genotypes_hk_bundle(
    case_id: str, timestamp, case_qc_metrics: Path, bcf_file: Path
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


@pytest.fixture(name="analysis_obj")
def fixture_analysis_obj(
    analysis_store_trio: Store, case_id: str, timestamp: datetime, helpers
) -> models.Analysis:
    """Return a analysis object with a trio"""
    family_obj = analysis_store_trio.family(case_id)
    helpers.add_analysis(store=analysis_store_trio, family=family_obj, started_at=timestamp)
    return analysis_store_trio.family(case_id).analyses[0]


@pytest.yield_fixture(name="upload_genotypes_api")
def fixture_upload_genotypes_api(
    real_housekeeper_api, genotype_api, upload_genotypes_hk_bundle, helpers
) -> UploadGenotypesAPI:
    """Create a upload genotypes api"""
    helpers.ensure_hk_bundle(real_housekeeper_api, upload_genotypes_hk_bundle, include=True)
    _api = UploadGenotypesAPI(
        hk_api=real_housekeeper_api,
        gt_api=genotype_api,
    )

    return _api


@pytest.yield_fixture(scope="function")
def upload_observations_api(analysis_store, populated_housekeeper_api):
    """ Create mocked UploadObservationsAPI object"""

    loqus_mock = MockLoqusAPI()

    _api = UploadObservationsAPI(
        status_api=analysis_store,
        hk_api=populated_housekeeper_api,
        loqus_api=loqus_mock,
    )

    yield _api


@pytest.yield_fixture(scope="function")
def upload_observations_api_wes(analysis_store, populated_housekeeper_api):
    """ Create mocked UploadObservationsAPI object"""

    loqus_mock = MockLoqusAPI(analysis_type="wes")

    _api = UploadObservationsAPI(
        status_api=analysis_store,
        hk_api=populated_housekeeper_api,
        loqus_api=loqus_mock,
    )

    yield _api


@pytest.yield_fixture(scope="function")
def upload_scout_api(scout_api, madeline_api, lims_samples, populated_housekeeper_api):
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


@pytest.yield_fixture(scope="function")
def mutacc_upload_api():
    """
    Fixture for a mutacc upload api
    """

    scout_api = MockScoutApi()
    mutacc_auto_api = MockMutaccAuto()

    _api = UploadToMutaccAPI(scout_api=scout_api, mutacc_auto_api=mutacc_auto_api)

    return _api


@pytest.yield_fixture(scope="function")
def coverage_upload_api(chanjo_config_dict, populated_housekeeper_api):
    """Fixture for coverage upload API"""
    hk_api = populated_housekeeper_api
    status_api = None
    coverage_api = MockCoverage(chanjo_config_dict)
    _api = UploadCoverageApi(status_api=status_api, hk_api=hk_api, chanjo_api=coverage_api)
    return _api


@pytest.yield_fixture(scope="function")
def analysis(analysis_store, case_id):
    """Fixture to mock an analysis"""
    _analysis = analysis_store.add_analysis(pipeline=Pipeline.BALSAMIC, version="version")
    _analysis.family = analysis_store.family(case_id)
    _analysis.config_path = "dummy_path"
    yield _analysis
