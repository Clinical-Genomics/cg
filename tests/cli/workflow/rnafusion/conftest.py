"""Fixtures for cli workflow rnafusion tests"""

import datetime as dt
import gzip
from pathlib import Path
from typing import List

import pytest

from cg.apps.hermes.hermes_api import HermesApi
from cg.apps.housekeeper.hk import HousekeeperAPI
from cg.constants import Pipeline
from cg.constants.constants import FileFormat
from cg.io.controller import WriteFile, WriteStream
from cg.meta.workflow.rnafusion import RnafusionAnalysisAPI
from cg.models.cg_config import CGConfig
from cg.store import Store, models
from tests.mocks.limsmock import MockLimsAPI
from tests.mocks.process_mock import ProcessMock
from tests.mocks.tb_mock import MockTB
from tests.store_helpers import StoreHelpers


@pytest.fixture(name="rnafusion_dir")
def rnafusion_dir(tmpdir_factory, apps_dir: Path) -> str:
    """Return the path to the rnafusion apps dir."""
    rnafusion_dir = tmpdir_factory.mktemp("rnafusion")
    return Path(rnafusion_dir).absolute().as_posix()


@pytest.fixture(name="rnafusion_case_id")
def fixture_rnafusion_case_id() -> str:
    """Returns a rnafusion case id."""
    return "rnafusion_case_enough_reads"


@pytest.fixture(name="no_sample_case_id")
def fixture_no_sample_case_id() -> str:
    """Returns a case id of a case with no samples."""
    return "no_sample_case"


@pytest.fixture(name="not_existing_case_id")
def fixture_not_existing_case_id() -> str:
    """Returns a case id not existing in dbs."""
    return "soberelephant"


@pytest.fixture(name="rnafusion_sample_id")
def fixture_rnafusion_sample_id() -> str:
    """Returns a rnafusion sample id."""
    return "sample_rnafusion_case_enough_reads"


@pytest.fixture(name="rnafusion_housekeeper_dir")
def rnafusion_housekeeper_dir(tmpdir_factory, rnafusion_dir: Path) -> Path:
    """Return the path to the rnafusion housekeeper bundle dir."""
    return tmpdir_factory.mktemp("bundles")


@pytest.fixture(name="rnafusion_reference_path")
def rnafusion_reference_path(rnafusion_dir: Path) -> str:
    rnafusion_reference_path = Path(rnafusion_dir, "references")
    rnafusion_reference_path.touch(exist_ok=True)
    return rnafusion_reference_path.as_posix()


@pytest.fixture
def rnafusion_fastq_file_l_1_r_1(rnafusion_housekeeper_dir: Path) -> str:
    fastq_filename = Path(
        rnafusion_housekeeper_dir, "XXXXXXXXX_000000_S000_L001_R1_001.fastq.gz"
    ).as_posix()
    with gzip.open(fastq_filename, "wb") as wh:
        wh.write(b"@A00689:73:XXXXXXXXX:1:1101:4806:1047 1:N:0:TCCTGGAACA+ACAACCAGTA")
    return fastq_filename


@pytest.fixture
def rnafusion_fastq_file_l_1_r_2(rnafusion_housekeeper_dir: Path) -> str:
    fastq_filename = Path(
        rnafusion_housekeeper_dir, "XXXXXXXXX_000000_S000_L001_R2_001.fastq.gz"
    ).as_posix()
    with gzip.open(fastq_filename, "wb") as wh:
        wh.write(b"@A00689:73:XXXXXXXXX:1:1101:4806:1047 2:N:0:TCCTGGAACA+ACAACCAGTA")
    return fastq_filename


@pytest.fixture
def rnafusion_mock_fastq_files(
    rnafusion_fastq_file_l_1_r_1: Path, rnafusion_fastq_file_l_1_r_2: Path
) -> List[Path]:
    """Return list of all mock fastq files to commit to mock housekeeper"""
    return [rnafusion_fastq_file_l_1_r_1, rnafusion_fastq_file_l_1_r_2]


@pytest.fixture(scope="function", name="rnafusion_housekeeper")
def rnafusion_housekeeper(
    housekeeper_api: HousekeeperAPI,
    helpers: StoreHelpers,
    rnafusion_mock_fastq_files: List[Path],
    rnafusion_sample_id: str,
):
    """Create populated housekeeper that holds files for all mock samples."""

    bundle_data = {
        "name": rnafusion_sample_id,
        "created": dt.datetime.now(),
        "version": "1.0",
        "files": [
            {"path": f, "tags": ["fastq"], "archive": False} for f in rnafusion_mock_fastq_files
        ],
    }
    helpers.ensure_hk_bundle(store=housekeeper_api, bundle_data=bundle_data)
    return housekeeper_api


@pytest.fixture(scope="function", name="rnafusion_context")
def fixture_rnafusion_context(
    cg_context: CGConfig,
    helpers: StoreHelpers,
    rnafusion_housekeeper: HousekeeperAPI,
    trailblazer_api: MockTB,
    hermes_api: HermesApi,
    cg_dir: Path,
    rnafusion_case_id: str,
    rnafusion_sample_id: str,
    no_sample_case_id: str,
) -> CGConfig:
    """context to use in cli"""
    cg_context.housekeeper_api_ = rnafusion_housekeeper
    cg_context.trailblazer_api_ = trailblazer_api
    cg_context.meta_apis["analysis_api"] = RnafusionAnalysisAPI(config=cg_context)
    status_db: Store = cg_context.status_db

    # Create ERROR case with NO SAMPLES
    helpers.add_case(status_db, internal_id=no_sample_case_id, name=no_sample_case_id)

    # Create textbook case with enough reads
    case_enough_reads: models.Family = helpers.add_case(
        store=status_db,
        internal_id=rnafusion_case_id,
        name=rnafusion_case_id,
        data_analysis=Pipeline.RNAFUSION,
    )

    sample_rnafusion_case_enough_reads: models.Sample = helpers.add_sample(
        status_db,
        internal_id=rnafusion_sample_id,
        sequenced_at=dt.datetime.now(),
    )

    helpers.add_relationship(
        status_db,
        case=case_enough_reads,
        sample=sample_rnafusion_case_enough_reads,
    )
    return cg_context


@pytest.fixture(name="deliverable_data")
def fixture_deliverables_data(
    rnafusion_dir: Path, rnafusion_case_id: str, rnafusion_sample_id: str
) -> dict:

    return {
        "files": [
            {
                "path": f"{rnafusion_dir}/{rnafusion_case_id}/multiqc/multiqc_report.html",
                "path_index": "",
                "step": "multiqc",
                "tag": ["qc"],
                "id": rnafusion_sample_id,
                "format": "html",
                "mandatory": True,
            },
        ]
    }


@pytest.fixture
def mock_deliverable(rnafusion_dir: Path, deliverable_data: dict, rnafusion_case_id: str) -> None:
    """Create deliverable file with dummy data and files to deliver."""
    Path.mkdir(
        Path(rnafusion_dir, rnafusion_case_id),
        parents=True,
        exist_ok=True,
    )
    Path.mkdir(
        Path(rnafusion_dir, rnafusion_case_id, "multiqc"),
        parents=True,
        exist_ok=True,
    )
    for report_entry in deliverable_data["files"]:
        Path(report_entry["path"]).touch(exist_ok=True)
    WriteFile.write_file_from_content(
        content=deliverable_data,
        file_format=FileFormat.JSON,
        file_path=Path(rnafusion_dir, rnafusion_case_id, rnafusion_case_id + "_deliverables.yaml"),
    )


@pytest.fixture(name="hermes_deliverables")
def fixture_hermes_deliverables(deliverable_data: dict, rnafusion_case_id: str) -> dict:
    hermes_output: dict = {"pipeline": "rnafusion", "bundle_id": rnafusion_case_id, "files": []}
    for file_info in deliverable_data["files"]:
        tags: List[str] = []
        if "html" in file_info["format"]:
            tags.append("multiqc-html")
        hermes_output["files"].append({"path": file_info["path"], "tags": tags, "mandatory": True})
    return hermes_output


@pytest.fixture(name="malformed_hermes_deliverables")
def fixture_malformed_hermes_deliverables(hermes_deliverables: dict) -> dict:
    malformed_deliverable: dict = hermes_deliverables.copy()
    malformed_deliverable.pop("pipeline")

    return malformed_deliverable


@pytest.fixture(name="rnafusion_hermes_process")
def fixture_rnafusion_hermes_process(
    hermes_deliverables: dict, process: ProcessMock
) -> ProcessMock:
    """Return a process mock populated with some rnafusion hermes output."""
    process.set_stdout(
        text=WriteStream.write_stream_from_content(
            content=hermes_deliverables, file_format=FileFormat.JSON
        )
    )
    return process


@pytest.fixture
def mock_analysis_finish(rnafusion_dir: Path, rnafusion_case_id: str) -> None:
    """Create analysis_finish file for testing"""
    Path.mkdir(Path(rnafusion_dir, rnafusion_case_id, "pipeline_info"), parents=True, exist_ok=True)
    Path(rnafusion_dir, rnafusion_case_id, "pipeline_info", "software_versions.yml").touch(
        exist_ok=True
    )


@pytest.fixture
def mock_config(rnafusion_dir: Path, rnafusion_case_id: str) -> None:
    """Create samplesheet.csv file for testing"""
    Path.mkdir(Path(rnafusion_dir, rnafusion_case_id), parents=True, exist_ok=True)
    Path(rnafusion_dir, rnafusion_case_id, f"{rnafusion_case_id}_samplesheet.csv").touch(
        exist_ok=True
    )
