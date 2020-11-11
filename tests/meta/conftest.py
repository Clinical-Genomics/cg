"""Fixtures for the meta tests"""

from datetime import datetime
from pathlib import Path

import pytest
from _pytest import tmpdir

from cg.store import Store
from cg.apps.balsamic.fastq import FastqHandler as BalsamicFastqHandler
from cg.apps.microsalt.fastq import FastqHandler as MicrosaltFastqHandler
from cg.apps.hk import HousekeeperAPI
from cg.apps.scoutapi import ScoutAPI
from cg.meta.workflow.mip import MipAnalysisAPI

from tests.store_helpers import StoreHelpers


@pytest.yield_fixture(scope="function", name="analysis_store")
def fixture_analysis_store(base_store: Store, analysis_family: dict) -> Store:
    """Setup a store instance for testing analysis API."""
    customer = base_store.customer("cust000")
    family = base_store.Family(
        data_analysis=analysis_family["data_analysis"],
        name=analysis_family["name"],
        panels=analysis_family["panels"],
        internal_id=analysis_family["internal_id"],
        priority="standard",
    )
    family.customer = customer
    base_store.add(family)
    application_version = base_store.application("WGTPCFC030").versions[0]
    for sample_data in analysis_family["samples"]:
        sample = base_store.add_sample(
            name=sample_data["name"],
            sex=sample_data["sex"],
            internal_id=sample_data["internal_id"],
            ticket=sample_data["ticket_number"],
            reads=sample_data["reads"],
            capture_kit=sample_data["capture_kit"],
        )
        sample.family = family
        sample.application_version = application_version
        sample.customer = customer
        base_store.add(sample)
    base_store.commit()
    for sample_data in analysis_family["samples"]:
        sample_obj = base_store.sample(sample_data["internal_id"])
        link = base_store.relate_sample(
            family=family,
            sample=sample_obj,
            status=sample_data["status"],
            father=base_store.sample(sample_data["father"]) if sample_data.get("father") else None,
            mother=base_store.sample(sample_data["mother"]) if sample_data.get("mother") else None,
        )
        base_store.add(link)
    base_store.commit()
    yield base_store


class MockLims:
    """Mock lims fixture"""

    lims = None

    def __init__(self):
        self.lims = self


class MockPath:
    def __init__(self, path):
        self.yaml = None

    def __call__(self, *args, **kwargs):
        return self

    def open(self):
        return dict()

    def joinpath(self, path):
        return path


class MockLogger:
    warnings = []

    def warning(self, text, *interpolations):

        self.warnings.append(text % interpolations)

    def get_warnings(self) -> list:
        return self.warnings


class MockTB:
    _get_trending_raises_keyerror = False

    def __init__(self):
        """Needed to initialise mock variables"""
        self._make_config_was_called = False

    def get_trending(self, mip_config_raw: dict, qcmetrics_raw: dict, sampleinfo_raw: dict) -> dict:
        if self._get_trending_raises_keyerror:
            raise KeyError("mockmessage")

        # Returns: dict: parsed data
        ### Define output dict
        outdata = {
            "analysis_sex": {"ADM1": "female", "ADM2": "female", "ADM3": "female"},
            "family": "yellowhog",
            "duplicates": {"ADM1": 13.525, "ADM2": 12.525, "ADM3": 14.525},
            "genome_build": "hg19",
            "mapped_reads": {"ADM1": 98.8, "ADM2": 99.8, "ADM3": 97.8},
            "mip_version": "v4.0.20",
            "sample_ids": ["2018-20203", "2018-20204"],
            "genome_build": "37",
            "rank_model_version": "1.18",
        }

        return outdata

    def get_sampleinfo(self, analysis_obj):
        return ""

    def make_config(self, data, pipeline):
        """Mock the make_config"""
        self._make_config_was_called = True
        del pipeline
        return data


class MockBalsamicFastq(BalsamicFastqHandler):
    """Mock FastqHandler for analysis_api"""

    def __init__(self):
        super().__init__(config={"balsamic": {"root": tmpdir}})


class MockMicrosaltFastq(MicrosaltFastqHandler):
    """Mock FastqHandler for analysis_api"""

    def __init__(self):
        super().__init__(config={"microsalt": {"root": tmpdir}})


@pytest.yield_fixture(scope="function", name="mip_hk_store")
def fixture_mip_hk_store(
    helpers: StoreHelpers,
    real_housekeeper_api: HousekeeperAPI,
    timestamp: datetime,
    case_id: str,
) -> HousekeeperAPI:
    deliver_hk_bundle_data = {
        "name": case_id,
        "created": timestamp,
        "expires": timestamp,
        "files": [
            {
                "path": "tests/fixtures/apps/mip/dna/store/case_config.yaml",
                "archive": False,
                "tags": ["mip-config"],
            },
            {
                "path": "tests/fixtures/apps/mip/dna/store/case_qc_sample_info.yaml",
                "archive": False,
                "tags": ["sampleinfo"],
            },
            {
                "path": "tests/fixtures/apps/mip/case_qc_metrics.yaml",
                "archive": False,
                "tags": ["qcmetrics"],
            },
            {
                "path": "tests/fixtures/apps/mip/case_file.txt",
                "archive": False,
                "tags": ["case-tag"],
            },
            {
                "path": "tests/fixtures/apps/mip/sample_file.txt",
                "archive": False,
                "tags": ["sample-tag", "ADM1"],
            },
        ],
    }
    helpers.ensure_hk_bundle(real_housekeeper_api, deliver_hk_bundle_data, include=True)

    empty_deliver_hk_bundle_data = {
        "name": "case_missing_data",
        "created": timestamp,
        "expires": timestamp,
        "files": [
            {
                "path": "tests/fixtures/apps/mip/dna/store/empty_case_config.yaml",
                "archive": False,
                "tags": ["mip-config"],
            },
            {
                "path": "tests/fixtures/apps/mip/dna/store/empty_case_qc_sample_info.yaml",
                "archive": False,
                "tags": ["sampleinfo"],
            },
            {
                "path": "tests/fixtures/apps/mip/dna/store/empty_case_qc_metrics.yaml",
                "archive": False,
                "tags": ["qcmetrics"],
            },
            {
                "path": "tests/fixtures/apps/mip/case_file.txt",
                "archive": False,
                "tags": ["case-tag"],
            },
            {
                "path": "tests/fixtures/apps/mip/sample_file.txt",
                "archive": False,
                "tags": ["sample-tag", "ADM1"],
            },
        ],
    }
    helpers.ensure_hk_bundle(real_housekeeper_api, empty_deliver_hk_bundle_data, include=True)

    return real_housekeeper_api


@pytest.yield_fixture(scope="function", name="analysis_api")
def fixture_analysis_api(
    analysis_store: Store, mip_hk_store: HousekeeperAPI, scout_api: ScoutAPI
) -> MipAnalysisAPI:
    """Setup an analysis API."""

    analysis_api = MipAnalysisAPI(
        db=analysis_store,
        hk_api=mip_hk_store,
        scout_api=scout_api,
        tb_api=MockTB(),
        lims_api=MockLims(),
        script="echo",
        pipeline="analyse rd_dna",
        conda_env="S_mip_rd-dna",
        root="/var/empty",
    )
    yield analysis_api
