"""Fixtures for the meta tests"""

import pytest
from _pytest import tmpdir

from cg.apps.balsamic.fastq import FastqHandler as BalsamicFastqHandler
from cg.apps.crunchy import CrunchyAPI
from cg.apps.tb import TrailblazerAPI
from cg.apps.microsalt.fastq import FastqHandler as MicrosaltFastqHandler
from cg.meta.deliver import DeliverAPI
from cg.meta.workflow.mip import AnalysisAPI
from tests.mocks.hk_mock import MockFile


@pytest.yield_fixture(scope="function")
def analysis_store(base_store, analysis_family):
    """Setup a store instance for testing analysis API."""
    customer = base_store.customer("cust000")
    family = base_store.Family(
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
            data_analysis=sample_data["data_analysis"],
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


class MockCrunchy(CrunchyAPI):

    pass


class MockLims:
    """Mock lims fixture"""

    lims = None

    def __init__(self):
        self.lims = self


class MockDeliver(DeliverAPI):
    def __init__(self):
        self.housekeeper = None
        self.lims = MockLims()

    def get_post_analysis_files(self, case: str, version, tags):

        if tags[0] == "mip-config":
            path = f"/mnt/hds/proj/bioinfo/bundles/{case}/2018-01-30/{case}_config.yaml"
        elif tags[0] == "sampleinfo":
            path = f"/mnt/hds/proj/bioinfo/bundles/{case}/2018-01-30/{case}_qc_sample_info.yaml"
        if tags[0] == "qcmetrics":
            path = f"/mnt/hds/proj/bioinfo/bundles/{case}/2018-01-30/{case}_qc_metrics.yaml"

        return [MockFile(path=path)]

    def get_post_analysis_case_files(self, case: str, version, tags):
        return ""

    def get_post_analysis_files_root_dir(self):
        return ""


class MockPath:
    def __init__(self, path):
        self.yaml = None

    def __call__(self, *args, **kwargs):
        return self

    def open(self):
        return dict()

    def joinpath(self, path):
        return ""


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


def safe_loader(path):
    """Mock function for loading yaml"""

    if path:
        pass

    return {
        "human_genome_build": {"version": ""},
        "recipe": {"rankvariant": {"rank_model": {"version": 1.18}}},
    }


@pytest.yield_fixture(scope="function")
def analysis_api(analysis_store, housekeeper_api, scout_api):
    """Setup an analysis API."""
    Path_mock = MockPath("")
    tb_mock = MockTB()
    deliver_mock = MockDeliver()
    deliver_mock.housekeeper = housekeeper_api

    _analysis_api = AnalysisAPI(
        db=analysis_store,
        hk_api=housekeeper_api,
        scout_api=scout_api,
        tb_api=tb_mock,
        lims_api=None,
        deliver_api=deliver_mock,
        yaml_loader=safe_loader,
        path_api=Path_mock,
        logger=MockLogger(),
        script="echo",
        pipeline="analyse rd_dna",
        conda_env="S_mip_rd-dna",
        root="/var/empty",
    )
    yield _analysis_api


@pytest.yield_fixture(scope="function")
def deliver_api(analysis_store, housekeeper_api, case_id, timestamp, helpers):
    """Fixture for deliver_api"""
    lims_mock = MockLims()
    hk_mock = housekeeper_api

    deliver_hk_bundle_data = {
        "name": case_id,
        "created": timestamp,
        "expires": timestamp,
        "files": [
            {"path": "/mock/path", "archive": False, "tags": ["case-tag"]},
            {"path": "/mock/path", "archive": False, "tags": ["sample-tag", "ADM1"]},
        ],
    }
    helpers.ensure_hk_bundle(hk_mock, deliver_hk_bundle_data)

    _api = DeliverAPI(
        db=analysis_store,
        hk_api=hk_mock,
        lims_api=lims_mock,
        case_tags=["case-tag"],
        sample_tags=["sample-tag"],
    )

    yield _api
