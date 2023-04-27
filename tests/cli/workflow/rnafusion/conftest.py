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
from cg.io.json import write_json
from cg.meta.workflow.rnafusion import RnafusionAnalysisAPI
from cg.models.cg_config import CGConfig
from cg.store import Store
from cg.store.models import Family, Sample
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
    case_enough_reads: Family = helpers.add_case(
        store=status_db,
        internal_id=rnafusion_case_id,
        name=rnafusion_case_id,
        data_analysis=Pipeline.RNAFUSION,
    )

    sample_rnafusion_case_enough_reads: Sample = helpers.add_sample(
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
                "step": "report",
                "tag": ["multiqc-html", "rna"],
                "id": rnafusion_case_id,
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
def rnafusion_metrics_deliverables(rnafusion_case_id: str) -> dict:
    return {
        "report_data_sources": {},
        "report_general_stats_data": [
            {rnafusion_case_id: {"5_3_bias": 1.07, "reads_aligned": 72391566.0}},
            {
                rnafusion_case_id: {
                    "PF_BASES": 14818118467.0,
                    "PF_ALIGNED_BASES": 14216931956.0,
                    "RIBOSOMAL_BASES": 93556030.0,
                    "CODING_BASES": 8123651685.0,
                    "UTR_BASES": 4099091115.0,
                    "INTRONIC_BASES": 1642902977.0,
                    "INTERGENIC_BASES": 257730149.0,
                    "IGNORED_READS": 0.0,
                    "CORRECT_STRAND_READS": 97603146.0,
                    "INCORRECT_STRAND_READS": 1111278.0,
                    "NUM_R1_TRANSCRIPT_STRAND_READS": 514532.0,
                    "NUM_R2_TRANSCRIPT_STRAND_READS": 48254438.0,
                    "NUM_UNEXPLAINED_READS": 679669.0,
                    "PCT_R1_TRANSCRIPT_STRAND_READS": 1.055,
                    "PCT_R2_TRANSCRIPT_STRAND_READS": 98.94500000000001,
                    "PCT_RIBOSOMAL_BASES": 0.6581,
                    "PCT_CODING_BASES": 57.1407,
                    "PCT_UTR_BASES": 28.8325,
                    "PCT_INTRONIC_BASES": 11.556,
                    "PCT_INTERGENIC_BASES": 1.8127999999999997,
                    "PCT_MRNA_BASES": 85.9731,
                    "PCT_USABLE_BASES": 82.4851,
                    "PCT_CORRECT_STRAND_READS": 98.8742,
                    "MEDIAN_CV_COVERAGE": 0.396435,
                    "MEDIAN_5PRIME_BIAS": 0.784592,
                    "MEDIAN_3PRIME_BIAS": 0.61818,
                    "MEDIAN_5PRIME_TO_3PRIME_BIAS": 1.1211,
                    "SAMPLE": "",
                    "LIBRARY": "",
                    "READ_GROUP": "",
                    "PF_NOT_ALIGNED_BASES": 601186511.0,
                }
            },
            {
                rnafusion_case_id: {
                    "LIBRARY": "Unknown Library",
                    "UNPAIRED_READS_EXAMINED": 589.0,
                    "READ_PAIRS_EXAMINED": 72391566.0,
                    "SECONDARY_OR_SUPPLEMENTARY_RDS": 15955495.0,
                    "UNMAPPED_READS": 4330483.0,
                    "UNPAIRED_READ_DUPLICATES": 410.0,
                    "READ_PAIR_DUPLICATES": 20682015.0,
                    "READ_PAIR_OPTICAL_DUPLICATES": 341387.0,
                    "PERCENT_DUPLICATION": 0.285698,
                    "ESTIMATED_LIBRARY_SIZE": 102249865.0,
                }
            },
            {
                rnafusion_case_id: {
                    "total_reads": 74557102.0,
                    "avg_input_read_length": 198.0,
                    "uniquely_mapped": 67865050.0,
                    "uniquely_mapped_percent": 91.02,
                    "avg_mapped_read_length": 196.52,
                    "num_splices": 42343777.0,
                    "num_annotated_splices": 42293347.0,
                    "num_GTAG_splices": 41860003.0,
                    "num_GCAG_splices": 401760.0,
                    "num_ATAC_splices": 34732.0,
                    "num_noncanonical_splices": 47282.0,
                    "mismatch_rate": 0.34,
                    "deletion_rate": 0.0,
                    "deletion_length": 1.26,
                    "insertion_rate": 0.01,
                    "insertion_length": 1.75,
                    "multimapped": 4527105.0,
                    "multimapped_percent": 6.07,
                    "multimapped_toomany": 33497.0,
                    "multimapped_toomany_percent": 0.04,
                    "unmapped_mismatches_percent": 0.26,
                    "unmapped_tooshort_percent": 2.56,
                    "unmapped_other_percent": 0.04,
                    "unmapped_mismatches": 193768,
                    "unmapped_tooshort": 1907871,
                    "unmapped_other": 29810,
                }
            },
            {
                rnafusion_case_id: {
                    "filtering_result_passed_filter_reads": 149114204.0,
                    "filtering_result_low_quality_reads": 855796.0,
                    "filtering_result_too_many_N_reads": 4992.0,
                    "filtering_result_too_short_reads": 9050.0,
                    "filtering_result_too_long_reads": 0.0,
                    "pct_duplication": 14.8643,
                    "after_filtering_total_reads": 149114204.0,
                    "after_filtering_total_bases": 14818118467.0,
                    "after_filtering_q20_bases": 14445202304.0,
                    "after_filtering_q30_bases": 13773086666.0,
                    "after_filtering_q20_rate": 0.974834,
                    "after_filtering_q30_rate": 0.929476,
                    "after_filtering_read1_mean_length": 99.0,
                    "after_filtering_read2_mean_length": 99.0,
                    "after_filtering_gc_content": 0.516984,
                    "before_filtering_total_reads": 149984042.0,
                    "pct_surviving": 99.42004630065911,
                    "adapter_cutting_adapter_trimmed_reads": 18006566.0,
                    "adapter_cutting_adapter_trimmed_bases": 228026691.0,
                    "pct_adapter": 12.005654574904709,
                }
            },
            {
                f"{rnafusion_case_id}_1": {
                    "percent_gc": 51.0,
                    "avg_sequence_length": 98.42709962090532,
                    "median_sequence_length": 100,
                    "total_sequences": 74557102.0,
                    "percent_duplicates": 64.54554620264767,
                    "percent_fails": 18.181818181818183,
                },
                f"{rnafusion_case_id}_2": {
                    "percent_gc": 51.0,
                    "avg_sequence_length": 151.0,
                    "median_sequence_length": 151,
                    "total_sequences": 74992021.0,
                    "percent_duplicates": 65.06134207022326,
                    "percent_fails": 27.27272727272727,
                },
            },
        ],
        "report_general_stats_headers": [],
    }


@pytest.fixture
def mock_analysis_finish(
    rnafusion_dir: Path, rnafusion_case_id: str, rnafusion_metrics_deliverables: dict
) -> None:
    """Create analysis_finish file for testing"""
    Path.mkdir(Path(rnafusion_dir, rnafusion_case_id, "pipeline_info"), parents=True, exist_ok=True)
    Path(rnafusion_dir, rnafusion_case_id, "pipeline_info", "software_versions.yml").touch(
        exist_ok=True
    )
    Path(rnafusion_dir, rnafusion_case_id, f"{rnafusion_case_id}_samplesheet.csv").touch(
        exist_ok=True
    )
    Path.mkdir(
        Path(rnafusion_dir, rnafusion_case_id, "multiqc", "multiqc_data"),
        parents=True,
        exist_ok=True,
    )
    write_json(
        content=rnafusion_metrics_deliverables,
        file_path=Path(
            rnafusion_dir,
            rnafusion_case_id,
            "multiqc",
            "multiqc_data",
            "multiqc_data.json",
        ),
    )


@pytest.fixture
def mock_config(rnafusion_dir: Path, rnafusion_case_id: str) -> None:
    """Create samplesheet.csv file for testing"""
    Path.mkdir(Path(rnafusion_dir, rnafusion_case_id), parents=True, exist_ok=True)
    Path(rnafusion_dir, rnafusion_case_id, f"{rnafusion_case_id}_samplesheet.csv").touch(
        exist_ok=True
    )
