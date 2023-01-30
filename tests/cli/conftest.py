"""Fixtures for cli tests."""
from pathlib import Path
from typing import Dict, Any

import pytest

from cg.apps.crunchy import CrunchyAPI
from cg.apps.housekeeper.hk import HousekeeperAPI
from cg.meta.compress import CompressAPI
from cg.models.cg_config import CGConfig
from cg.store import Store
from click.testing import CliRunner

from tests.cli.compress.conftest import CaseInfo
from tests.store_helpers import StoreHelpers


@pytest.fixture(name="cli_runner")
def fixture_cli_runner() -> CliRunner:
    """Create a CliRunner"""
    return CliRunner()


@pytest.fixture(name="application_tag")
def fixture_application_tag() -> str:
    """Return a dummy tag"""
    return "dummy_tag"


@pytest.fixture(name="base_context")
def fixture_base_context(
    base_store: Store, housekeeper_api: HousekeeperAPI, cg_config_object: CGConfig
) -> CGConfig:
    """context to use in cli"""
    cg_config_object.status_db_ = base_store
    cg_config_object.housekeeper_api_ = housekeeper_api
    return cg_config_object


@pytest.fixture(name="before_date")
def fixture_before_date() -> str:
    """Return a before date string"""
    return "1999-12-31"


@pytest.fixture(name="disk_store")
def fixture_disk_store(base_context: CGConfig) -> Store:
    """context to use in cli"""
    return base_context.status_db


class MockCompressAPI(CompressAPI):
    """Mock out necessary functions for running the compress CLI functions."""

    def __init__(self):
        """initialize mock"""
        super().__init__(hk_api=None, crunchy_api=None, demux_root="")
        self.ntasks = 12
        self.mem = 50
        self.fastq_compression_success = True
        self.spring_decompression_success = True
        self.dry_run = False

    def set_dry_run(self, dry_run: bool):
        """Update dry run."""
        self.dry_run = dry_run

    def compress_fastq(self, sample_id: str, dry_run: bool = False):
        """Return if compression was successful."""
        _ = sample_id, dry_run
        return self.fastq_compression_success

    def decompress_spring(self, sample_id: str, dry_run: bool = False):
        """Return if decompression was succesful."""
        _ = sample_id, dry_run
        return self.spring_decompression_success


@pytest.fixture(name="compress_api")
def fixture_compress_api():
    """Return a compress API context."""
    return MockCompressAPI()


@pytest.fixture(name="compress_context")
def fixture_base_compress_context(
    compress_api: CompressAPI, store: Store, cg_config_object: CGConfig
) -> CGConfig:
    """Return a compress context."""
    cg_config_object.meta_apis["compress_api"] = compress_api
    cg_config_object.status_db_ = store
    return cg_config_object


@pytest.fixture(name="compress_case_info")
def fixture_compress_case_info(
    case_id,
    family_name,
    timestamp,
    later_timestamp,
    wgs_application_tag,
):
    """Returns a object with information about a case."""
    return CaseInfo(
        case_id=case_id,
        family_name=family_name,
        timestamp=timestamp,
        later_timestamp=later_timestamp,
        application_tag=wgs_application_tag,
    )


@pytest.fixture(name="populated_compress_store")
def fixture_populated_compress_store(store, helpers, compress_case_info, analysis_family):
    """Return a store populated with a completed analysis."""
    # Make sure that there is a case where analysis is completed
    helpers.ensure_case_from_dict(
        store,
        case_info=analysis_family,
        app_tag=compress_case_info.application_tag,
        ordered_at=compress_case_info.timestamp,
        completed_at=compress_case_info.later_timestamp,
    )
    return store


@pytest.fixture(name="populated_compress_context")
def fixture_populated_compress_context(
    compress_api: CompressAPI, populated_compress_store: Store, cg_config_object: CGConfig
) -> CGConfig:
    """Return a compress context populated with a completed analysis."""
    # Make sure that there is a case where analysis is completed
    cg_config_object.meta_apis["compress_api"] = compress_api
    cg_config_object.status_db_ = populated_compress_store
    return cg_config_object


@pytest.fixture(name="real_crunchy_api")
def fixture_real_crunchy_api(crunchy_config: Dict[str, Dict[str, Any]]):
    """Return Crunchy API."""
    _api = CrunchyAPI(crunchy_config)
    _api.set_dry_run(True)
    yield _api


@pytest.fixture(name="real_compress_api")
def fixture_real_compress_api(
    demultiplexed_runs: Path, housekeeper_api: HousekeeperAPI, real_crunchy_api: CrunchyAPI
) -> CompressAPI:
    """Return a compress API context."""
    return CompressAPI(
        crunchy_api=real_crunchy_api,
        hk_api=housekeeper_api,
        demux_root=demultiplexed_runs.as_posix(),
    )


@pytest.fixture(name="real_populated_compress_fastq_api")
def fixture_real_populated_compress_fastq_api(
    real_compress_api: CompressAPI, compress_hk_fastq_bundle: dict, helpers: StoreHelpers
) -> CompressAPI:
    """Return real populated compress API."""
    helpers.ensure_hk_bundle(real_compress_api.hk_api, compress_hk_fastq_bundle)

    return real_compress_api


@pytest.fixture(name="real_populated_compress_context")
def fixture_real_populated_compress_context(
    real_populated_compress_fastq_api: CompressAPI,
    populated_compress_store: Store,
    cg_config_object: CGConfig,
) -> CGConfig:
    """Return a compress context populated with a completed analysis."""
    # Make sure that there is a case where analysis is completed
    cg_config_object.meta_apis["compress_api"] = real_populated_compress_fastq_api
    cg_config_object.status_db_ = populated_compress_store
    return cg_config_object
