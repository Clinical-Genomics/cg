"""Fixtures for cli Compress functions."""

import datetime as dt
from datetime import datetime
from pathlib import Path
from typing import Any, Generator

import pytest

from cg.apps.crunchy import CrunchyAPI
from cg.apps.housekeeper.hk import HousekeeperAPI
from cg.constants import FileExtensions, SequencingFileTag
from cg.constants.pedigree import Pedigree
from cg.meta.compress import CompressAPI
from cg.models.cg_config import CGConfig
from cg.store.store import Store
from tests.store_helpers import StoreHelpers


class MockCompressAPI(CompressAPI):
    """Mock out necessary functions for running the compress CLI functions."""

    def __init__(self):
        """initialize mock."""
        super().__init__(hk_api=None, crunchy_api=None, demux_root="")
        self.fastq_compression_success: bool = True
        self.spring_decompression_success: bool = True
        self.dry_run: bool = False

    def set_dry_run(self, dry_run: bool) -> None:
        """Update dry run."""
        self.dry_run = dry_run

    def compress_fastq(self, sample_id: str, dry_run: bool = False) -> None:
        """Return if compression was successful."""
        _ = sample_id, dry_run
        return self.fastq_compression_success

    def decompress_spring(self, sample_id: str, dry_run: bool = False) -> None:
        """Return if decompression was successful."""
        _ = sample_id, dry_run
        return self.spring_decompression_success


@pytest.fixture
def compress_api() -> MockCompressAPI:
    """Return a Compress context."""
    return MockCompressAPI()


@pytest.fixture
def real_crunchy_api(
    crunchy_config: dict[str, dict[str, Any]]
) -> Generator[CrunchyAPI, None, None]:
    """Return Crunchy API."""
    _api = CrunchyAPI(crunchy_config)
    _api.set_dry_run(True)
    yield _api


@pytest.fixture
def real_compress_api(
    demultiplex_runs: Path, housekeeper_api: HousekeeperAPI, real_crunchy_api: CrunchyAPI
) -> CompressAPI:
    """Return a Compress context."""
    return CompressAPI(
        crunchy_api=real_crunchy_api, hk_api=housekeeper_api, demux_root=demultiplex_runs.as_posix()
    )


@pytest.fixture
def real_populated_compress_fastq_api(
    real_compress_api: CompressAPI, compress_hk_fastq_bundle: dict, helpers: StoreHelpers
) -> CompressAPI:
    """Return populated Compress API."""
    helpers.ensure_hk_bundle(real_compress_api.hk_api, compress_hk_fastq_bundle)
    return real_compress_api


# Store fixtures


class CaseInfo:
    """Holds information for creating a case."""

    def __init__(self, **kwargs):
        self.case_id: str = kwargs["case_id"]
        self.family_name: str = kwargs["family_name"]
        self.timestamp: datetime = kwargs["timestamp"]
        self.later_timestamp: datetime = kwargs["later_timestamp"]
        self.application_tag: str = kwargs["application_tag"]


@pytest.fixture
def compress_case_info(
    case_id: str,
    family_name: str,
    timestamp: datetime,
    later_timestamp: datetime,
    wgs_application_tag: str,
) -> CaseInfo:
    """Returns an object with information about a case."""
    return CaseInfo(
        case_id=case_id,
        family_name=family_name,
        timestamp=timestamp,
        later_timestamp=later_timestamp,
        application_tag=wgs_application_tag,
    )


@pytest.fixture
def populated_compress_store(
    store: Store, helpers: StoreHelpers, compress_case_info, analysis_family
):
    """Return a store populated with a completed analysis."""
    helpers.ensure_case_from_dict(
        store,
        case_info=analysis_family,
        app_tag=compress_case_info.application_tag,
        ordered_at=compress_case_info.timestamp,
        completed_at=compress_case_info.later_timestamp,
    )
    return store


@pytest.fixture
def populated_compress_multiple_store(
    store: Store,
    helpers: StoreHelpers,
    compress_case_info: CaseInfo,
    analysis_family: dict,
) -> Store:
    """Return a store populated with multiple completed analyses."""
    case_id: str = compress_case_info.case_id
    family_name: str = compress_case_info.family_name
    for number in range(10):
        analysis_family["internal_id"]: str = "_".join([str(number), case_id])
        analysis_family["name"]: str = "_".join([str(number), family_name])
        for ind, sample in enumerate(analysis_family["samples"]):
            analysis_family["samples"][ind]["internal_id"]: str = "_".join(
                [str(number), sample["internal_id"]]
            )
            if Pedigree.FATHER in analysis_family["samples"][ind]:
                analysis_family["samples"][ind][Pedigree.FATHER]: str = "_".join(
                    [str(number), analysis_family["samples"][ind][Pedigree.FATHER]]
                )
            if Pedigree.MOTHER in analysis_family["samples"][ind]:
                analysis_family["samples"][ind][Pedigree.MOTHER]: str = "_".join(
                    [str(number), analysis_family["samples"][ind][Pedigree.MOTHER]]
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
@pytest.fixture
def base_compress_context(
    compress_api: CompressAPI, store: Store, cg_config_object: CGConfig
) -> CGConfig:
    """Return a Compress context."""
    cg_config_object.meta_apis["compress_api"] = compress_api
    cg_config_object.status_db_ = store
    return cg_config_object


@pytest.fixture
def populated_multiple_compress_context(
    compress_api: CompressAPI, populated_compress_multiple_store: Store, cg_config_object: CGConfig
) -> CGConfig:
    """Return a Compress context populated with a completed analysis."""
    cg_config_object.meta_apis["compress_api"]: CompressAPI = compress_api
    cg_config_object.status_db_ = populated_compress_multiple_store
    return cg_config_object


@pytest.fixture
def populated_compress_context(
    compress_api: CompressAPI, populated_compress_store: Store, cg_config_object: CGConfig
) -> CGConfig:
    """Return a Compress context populated with a completed analysis."""
    cg_config_object.meta_apis["compress_api"]: CompressAPI = compress_api
    cg_config_object.status_db_ = populated_compress_store
    return cg_config_object


@pytest.fixture
def real_populated_compress_context(
    real_populated_compress_fastq_api: CompressAPI,
    populated_compress_store: Store,
    cg_config_object: CGConfig,
) -> CGConfig:
    """Return a Compress context populated with a completed analysis."""
    cg_config_object.meta_apis["compress_api"]: CompressAPI = real_populated_compress_fastq_api
    cg_config_object.status_db_ = populated_compress_store
    return cg_config_object


# Bundle fixtures


@pytest.fixture
def sample() -> str:
    """Return the sample id for first sample."""
    return "sample_1"


@pytest.fixture
def new_dir(project_dir: Path) -> Path:
    """Return the path to a subdirectory."""
    new_dir = Path(project_dir, "new_dir")
    new_dir.mkdir()
    return new_dir


@pytest.fixture
def spring_bundle(project_dir: Path, timestamp: datetime, sample: str) -> dict:
    """Return a bundle with spring files."""
    spring_file: Path = Path(project_dir, f"file{FileExtensions.SPRING}")
    spring_file.touch()
    spring_meta_file: Path = Path(project_dir, f"file{FileExtensions.JSON}")
    spring_meta_file.touch()
    return {
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


@pytest.fixture
def spring_bundle_symlink_problem(
    project_dir: Path, new_dir: Path, timestamp: datetime, sample: str
):
    """Return Housekeeper bundle with SPRING files having symlinks."""
    spring_file: Path = Path(project_dir, "file.spring")
    spring_file.touch()
    wrong_spring_file: Path = Path(new_dir, "file.spring")
    spring_meta_file: Path = Path(project_dir, "file.json")
    spring_meta_file.touch()
    wrong_spring_meta_file: Path = Path(new_dir, "file.json")
    return {
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


@pytest.fixture
def symlinked_fastqs(project_dir: Path, new_dir: Path) -> dict:
    """Setup an environment that is similar to the case we want to solve."""
    fastq_first: Path = Path(project_dir, "first.fastq.gz")
    fastq_second: Path = Path(project_dir, "second.fastq.gz")

    symlinked_first: Path = Path(new_dir, "first.fastq.gz")
    symlinked_first.symlink_to(fastq_first)
    symlinked_second: Path = Path(new_dir, "second.fastq.gz")
    symlinked_second.symlink_to(fastq_second)
    return {
        "fastq_first": fastq_first,
        "fastq_second": fastq_second,
        "symlinked_first": symlinked_first,
        "symlinked_second": symlinked_second,
    }
