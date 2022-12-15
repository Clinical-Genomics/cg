"""Fixtures for cli compress functions"""

import datetime as dt
from datetime import datetime
from pathlib import Path

import pytest

from cg.apps.crunchy import CrunchyAPI
from cg.apps.housekeeper.hk import HousekeeperAPI
from cg.constants import FileExtensions, SequencingFileTag
from cg.meta.compress import CompressAPI
from cg.models.cg_config import CGConfig
from cg.store import Store
from tests.store_helpers import StoreHelpers


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
        """Update dry run"""
        self.dry_run = dry_run

    def compress_fastq(self, sample_id: str, dry_run: bool = False):
        """Return if compression was succesfull"""
        _ = sample_id, dry_run
        return self.fastq_compression_success

    def decompress_spring(self, sample_id: str, dry_run: bool = False):
        """Return if decompression was succesfull"""
        _ = sample_id, dry_run
        return self.spring_decompression_success


@pytest.fixture(name="compress_api")
def fixture_compress_api():
    """Return a compress context"""
    return MockCompressAPI()


@pytest.fixture(scope="function", name="real_crunchy_api")
def fixture_real_crunchy_api(crunchy_config_dict):
    """crunchy api fixture"""
    _api = CrunchyAPI(crunchy_config_dict)
    _api.set_dry_run(True)
    yield _api


@pytest.fixture(scope="function", name="real_compress_api")
def fixture_real_compress_api(
    demultiplex_runs: Path, housekeeper_api: HousekeeperAPI, real_crunchy_api: CrunchyAPI
) -> CompressAPI:
    """Return a compress context"""
    return CompressAPI(
        crunchy_api=real_crunchy_api, hk_api=housekeeper_api, demux_root=demultiplex_runs.as_posix()
    )


@pytest.fixture(scope="function", name="real_populated_compress_fastq_api")
def fixture_real_populated_compress_fastq_api(
    real_compress_api: CompressAPI, compress_hk_fastq_bundle: dict, helpers: StoreHelpers
) -> CompressAPI:
    """Populated compress api fixture"""
    helpers.ensure_hk_bundle(real_compress_api.hk_api, compress_hk_fastq_bundle)

    return real_compress_api


@pytest.fixture(name="samples")
def fixture_samples():
    """Return a list of sample ids"""
    return ["sample1", "sample2", "sample3"]


# Store fixtures


class CaseInfo:
    """Holds information for creating a case"""

    def __init__(self, **kwargs):
        self.case_id = kwargs["case_id"]
        self.family_name = kwargs["family_name"]
        self.timestamp = kwargs["timestamp"]
        self.later_timestamp = kwargs["later_timestamp"]
        self.application_tag = kwargs["application_tag"]


@pytest.fixture(name="compress_case_info")
def fixture_compress_case_info(
    case_id,
    family_name,
    timestamp,
    later_timestamp,
    wgs_application_tag,
):
    """Returns a object with information about a case"""
    return CaseInfo(
        case_id=case_id,
        family_name=family_name,
        timestamp=timestamp,
        later_timestamp=later_timestamp,
        application_tag=wgs_application_tag,
    )


@pytest.fixture(name="populated_compress_store")
def fixture_populated_compress_store(store, helpers, compress_case_info, analysis_family):
    """Return a store populated with a completed analysis"""
    # Make sure that there is a case where anaylsis is completer
    helpers.ensure_case_from_dict(
        store,
        case_info=analysis_family,
        app_tag=compress_case_info.application_tag,
        ordered_at=compress_case_info.timestamp,
        completed_at=compress_case_info.later_timestamp,
    )

    return store


@pytest.fixture(name="populated_compress_multiple_store")
def fixture_populated_compress_multiple_store(
    store,
    helpers,
    compress_case_info,
    analysis_family,
):
    """Return a store populated with multiple completed analysis"""
    case_id = compress_case_info.case_id
    family_name = compress_case_info.family_name
    for number in range(10):
        analysis_family["internal_id"] = "_".join([str(number), case_id])
        analysis_family["name"] = "_".join([str(number), family_name])
        for ind, sample in enumerate(analysis_family["samples"]):
            analysis_family["samples"][ind]["internal_id"] = "_".join(
                [str(number), sample["internal_id"]]
            )
            if "father" in analysis_family["samples"][ind]:
                analysis_family["samples"][ind]["father"] = "_".join(
                    [str(number), analysis_family["samples"][ind]["father"]]
                )
            if "mother" in analysis_family["samples"][ind]:
                analysis_family["samples"][ind]["mother"] = "_".join(
                    [str(number), analysis_family["samples"][ind]["mother"]]
                )

        helpers.ensure_case_from_dict(
            store,
            case_info=analysis_family,
            app_tag=compress_case_info.application_tag,
            ordered_at=compress_case_info.timestamp,
            completed_at=compress_case_info.later_timestamp,
            created_at=dt.datetime.now() - dt.timedelta(days=1000),
        )
    return store


# Context fixtures
@pytest.fixture(name="compress_context")
def fixture_base_compress_context(
    compress_api: CompressAPI, store: Store, cg_config_object: CGConfig
) -> CGConfig:
    """Return a compress context"""
    cg_config_object.meta_apis["compress_api"] = compress_api
    cg_config_object.status_db_ = store
    return cg_config_object


@pytest.fixture(name="store_fastq_context")
def fixture_store_fastq_context(
    compress_api: CompressAPI, store: Store, cg_config_object: CGConfig
) -> CGConfig:
    """Return a compress context"""
    cg_config_object.meta_apis["compress_api"] = compress_api
    cg_config_object.status_db_ = store
    return cg_config_object


@pytest.fixture(name="populated_multiple_compress_context")
def fixture_populated_multiple_compress_context(
    compress_api: CompressAPI, populated_compress_multiple_store: Store, cg_config_object: CGConfig
) -> CGConfig:
    """Return a compress context populated with a completed analysis"""
    # Make sure that there is a case where anaylis is completer
    cg_config_object.meta_apis["compress_api"] = compress_api
    cg_config_object.status_db_ = populated_compress_multiple_store
    return cg_config_object


@pytest.fixture(name="populated_compress_context")
def fixture_populated_compress_context(
    compress_api: CompressAPI, populated_compress_store: Store, cg_config_object: CGConfig
) -> CGConfig:
    """Return a compress context populated with a completed analysis"""
    # Make sure that there is a case where analysis is completed
    cg_config_object.meta_apis["compress_api"] = compress_api
    cg_config_object.status_db_ = populated_compress_store
    return cg_config_object


@pytest.fixture(name="real_populated_compress_context")
def fixture_real_populated_compress_context(
    real_populated_compress_fastq_api: CompressAPI,
    populated_compress_store: Store,
    cg_config_object: CGConfig,
) -> CGConfig:
    """Return a compress context populated with a completed analysis"""
    # Make sure that there is a case where analysis is completed
    cg_config_object.meta_apis["compress_api"] = real_populated_compress_fastq_api
    cg_config_object.status_db_ = populated_compress_store
    return cg_config_object


# Bundle fixtures


@pytest.fixture(scope="function", name="sample")
def fixture_sample() -> str:
    """Return the sample id for first sample"""
    return "sample_1"


@pytest.fixture(scope="function", name="new_dir")
def fixture_new_dir(project_dir: Path) -> Path:
    """Return the path to a subdirectory"""
    new_dir = project_dir / "new_dir/"
    new_dir.mkdir()
    return new_dir


@pytest.fixture(name="spring_bundle")
def fixture_spring_bundle(project_dir: Path, timestamp: datetime, sample: str):
    """Return a bundle with spring files."""
    spring_file: Path = Path(project_dir, f"file{FileExtensions.SPRING}")
    spring_file.touch()
    spring_meta_file: Path = Path(project_dir, f"file{FileExtensions.JSON}")
    spring_meta_file.touch()
    hk_bundle_data = {
        "name": sample,
        "created": timestamp,
        "expires": timestamp,
        "files": [
            {
                "path": str(spring_file),
                "archive": False,
                "tags": [sample, SequencingFileTag.SPRING],
            },
            {
                "path": str(spring_meta_file),
                "archive": False,
                "tags": [sample, SequencingFileTag.SPRING_METADATA],
            },
        ],
    }

    return hk_bundle_data


@pytest.fixture(name="spring_bundle_symlink_problem")
def fixture_spring_bundle_symlink_problem(project_dir, new_dir, timestamp, sample):
    """Setup an environment that is similar to the case we want to solve"""
    # Create spring files and faulty paths to spring files
    spring_file = project_dir / "file.spring"
    spring_file.touch()
    wrong_spring_file = new_dir / "file.spring"
    spring_meta_file = project_dir / "file.json"
    spring_meta_file.touch()
    wrong_spring_meta_file = new_dir / "file.json"
    hk_bundle_data = {
        "name": sample,
        "created": timestamp,
        "expires": timestamp,
        "files": [
            {
                "path": str(wrong_spring_file),
                "archive": False,
                "tags": [sample, SequencingFileTag.SPRING],
            },
            {
                "path": str(wrong_spring_meta_file),
                "archive": False,
                "tags": [sample, SequencingFileTag.SPRING_METADATA],
            },
        ],
    }

    return hk_bundle_data


@pytest.fixture(name="symlinked_fastqs")
def fixture_symlinked_fastqs(project_dir: Path, new_dir: Path) -> dict:
    """Setup an environment that is similar to the case we want to solve"""
    fastq_first = project_dir / "first.fastq.gz"
    fastq_second = project_dir / "second.fastq.gz"

    symlinked_first = new_dir / "first.fastq.gz"
    symlinked_first.symlink_to(fastq_first)
    symlinked_second = new_dir / "second.fastq.gz"
    symlinked_second.symlink_to(fastq_second)
    return {
        "fastq_first": fastq_first,
        "fastq_second": fastq_second,
        "symlinked_first": symlinked_first,
        "symlinked_second": symlinked_second,
    }
