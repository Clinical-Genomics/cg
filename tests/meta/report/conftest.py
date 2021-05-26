import json
from datetime import datetime, timedelta
from typing import List

import pytest
from cg.meta.report.api import ReportAPI
from cg.store import Store
from tests.mocks.limsmock import MockLimsAPI


@pytest.fixture
def lims_family() -> dict:
    return json.load(open("tests/fixtures/report/lims_family.json"))


@pytest.fixture
def lims_samples(lims_family: dict) -> List[dict]:
    return lims_family["samples"]


@pytest.fixture
def report_samples(lims_family: List[dict]):
    for sample in lims_family["samples"]:
        sample["internal_id"] = sample["id"]

    return lims_family["samples"]


class MockFile:
    def __init__(self, path):
        self.path = path


class MockChanjo:
    _sample_coverage_returns_none = False

    def sample_coverage(self, sample_id: str, panel_genes: list) -> dict:
        """Calculate coverage for OMIM panel."""

        if self._sample_coverage_returns_none:
            return None

        if sample_id == "ADM1":
            data = {"mean_coverage": 38.342, "mean_completeness": 99.1}
        elif sample_id == "ADM2":
            data = {"mean_coverage": 37.342, "mean_completeness": 97.1}
        else:
            data = {"mean_coverage": 39.342, "mean_completeness": 98.1}

        return data

    def sample(self, sample_id: str) -> dict:
        """Fetch sample from the database."""
        return {"id": sample_id}


class MockPath:
    _path = None

    def __call__(self, path):
        self._path = path
        return self

    def joinpath(self, another_path):
        return self(self._path + another_path)

    def open(self):
        pass


class MockAnalysis:
    def panel(self, case_obj) -> [str]:
        """Create the aggregated panel file."""
        return [""]

    def get_latest_metadata(self, family_id):
        # Returns: dict: parsed data
        # Define output dict
        out_data = {
            "analysis_sex": {"ADM1": "female", "ADM2": "female", "ADM3": "female"},
            "family": "yellowhog",
            "duplicates": {"ADM1": 13.525, "ADM2": 12.525, "ADM3": 14.525},
            "genome_build": "hg19",
            "mapped_reads": {"ADM1": 98.8, "ADM2": 99.8, "ADM3": 97.8},
            "mip_version": "v4.0.20",
            "sample_ids": ["2018-20203", "2018-20204"],
        }

        return out_data


class MockLogger:
    last_warning = None
    warnings = []

    def warning(self, text, *interpolations):

        self.warnings.append(text % interpolations)
        self.last_warning = text % interpolations

    def get_last_warning(self) -> str:
        return self.last_warning

    def get_warnings(self) -> list:
        return self.warnings


class MockDB(Store):
    family_samples_returns_no_reads = False
    samples_returns_no_capture_kit = False
    _application_accreditation = None

    def __init__(self, store):
        self.store = store

    def family_samples(self, family_id: str):

        family_samples = self.store.family_samples(family_id)

        if self.family_samples_returns_no_reads:
            for family_sample in family_samples:
                family_sample.sample.reads = None

        if self.samples_returns_no_capture_kit:
            for family_sample in family_samples:
                family_sample.sample.capture_kit = None

        # add some date to calculate processing time on
        yesterday = datetime.now() - timedelta(days=1)
        for family_sample in family_samples:
            family_sample.sample.received_at = yesterday
            family_sample.sample.prepared_at = yesterday
            family_sample.sample.sequenced_at = yesterday
            family_sample.sample.delivered_at = datetime.now()

        return family_samples

    def application(self, tag: str):
        """Fetch an application from the store."""
        application = self.store.application(tag=tag)

        if self._application_accreditation is not None:
            application.is_accredited = self._application_accreditation

        return application


class MockScout:
    def get_genes(self, panel_id: str, version: str = None) -> list:
        return []


@pytest.fixture(scope="function")
def report_api(report_store, lims_samples):
    db = MockDB(report_store)
    lims = MockLimsAPI(samples=lims_samples)
    chanjo = MockChanjo()
    analysis = MockAnalysis()
    scout = MockScout()
    logger = MockLogger()
    path_tool = MockPath()
    return ReportAPI(
        lims_api=lims,
        store=db,
        chanjo_api=chanjo,
        analysis_api=analysis,
        scout_api=scout,
        logger=logger,
        path_tool=path_tool,
    )


@pytest.fixture(scope="function")
def report_store(analysis_store, helpers):
    family = analysis_store.families()[0]
    yesterday = datetime.now() - timedelta(days=1)
    helpers.add_analysis(analysis_store, family, started_at=yesterday)
    helpers.add_analysis(analysis_store, family, started_at=datetime.now())
    return analysis_store
