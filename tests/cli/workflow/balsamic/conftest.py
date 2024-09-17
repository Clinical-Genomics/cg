"""Fixtures for cli workflow balsamic tests"""

import datetime as dt
import gzip
from pathlib import Path

import pytest

from cg.apps.housekeeper.hk import HousekeeperAPI
from cg.constants import SequencingFileTag, Workflow
from cg.constants.constants import CaseActions, FileFormat, PrepCategory
from cg.io.controller import WriteFile
from cg.meta.workflow.balsamic import BalsamicAnalysisAPI
from cg.models.cg_config import CGConfig
from cg.store.models import ApplicationVersion, Sample
from cg.store.store import Store
from tests.mocks.limsmock import MockLimsAPI
from tests.mocks.tb_mock import MockTB
from tests.store_helpers import StoreHelpers


@pytest.fixture
def balsamic_dir(tmpdir_factory, apps_dir: Path) -> str:
    """Return the path to the balsamic apps dir"""
    balsamic_dir = tmpdir_factory.mktemp("balsamic")
    return Path(balsamic_dir).absolute().as_posix()


@pytest.fixture
def balsamic_case_id() -> str:
    return "balsamic_case_wgs_single"


@pytest.fixture
def balsamic_housekeeper_dir(tmpdir_factory, balsamic_dir: Path) -> Path:
    """Return the path to the balsamic housekeeper bundle dir."""
    return tmpdir_factory.mktemp("bundles")


@pytest.fixture
def balsamic_pon_1_path(balsamic_dir: Path) -> str:
    balsamic_reference_path = Path(balsamic_dir, "balsamic_bed_1_case_PON_reference.cnn")
    balsamic_reference_path.touch(exist_ok=True)
    return balsamic_reference_path.as_posix()


@pytest.fixture
def balsamic_bed_1_path(balsamic_dir: Path) -> str:
    balsamic_bed_1_path = Path(balsamic_dir, "balsamic_bed_1.bed")
    balsamic_bed_1_path.touch(exist_ok=True)
    return balsamic_bed_1_path.as_posix()


@pytest.fixture
def balsamic_bed_2_path(balsamic_dir: Path) -> str:
    balsamic_bed_2_path = Path(balsamic_dir, "balsamic_bed_2.bed")
    balsamic_bed_2_path.touch(exist_ok=True)
    return balsamic_bed_2_path.as_posix()


@pytest.fixture
def fastq_file_l_1_r_1(balsamic_housekeeper_dir: Path) -> str:
    fastq_filename = Path(
        balsamic_housekeeper_dir, "XXXXXXXXX_000000_S000_L001_R1_001.fastq.gz"
    ).as_posix()
    with gzip.open(fastq_filename, "wb") as wh:
        wh.write(b"@A00689:73:XXXXXXXXX:1:1101:4806:1047 1:N:0:TCCTGGAACA+ACAACCAGTA")
    return fastq_filename


@pytest.fixture
def fastq_file_l_2_r_1(balsamic_housekeeper_dir: Path) -> str:
    fastq_filename = Path(
        balsamic_housekeeper_dir, "XXXXXXXXX_000000_S000_L002_R1_001.fastq.gz"
    ).as_posix()
    with gzip.open(fastq_filename, "wb") as wh:
        wh.write(b"@A00689:73:XXXXXXXXX:2:1101:4806:1047 1:N:0:TCCTGGAACA+ACAACCAGTA")
    return fastq_filename


@pytest.fixture
def fastq_file_l_3_r_1(balsamic_housekeeper_dir: Path) -> str:
    fastq_filename = Path(
        balsamic_housekeeper_dir, "XXXXXXXXX_000000_S000_L003_R1_001.fastq.gz"
    ).as_posix()
    with gzip.open(fastq_filename, "wb") as wh:
        wh.write(b"@A00689:73:XXXXXXXXX:3:1101:4806:1047 1:N:0:TCCTGGAACA+ACAACCAGTA")
    return fastq_filename


@pytest.fixture
def fastq_file_l_4_r_1(balsamic_housekeeper_dir: Path) -> str:
    fastq_filename = Path(
        balsamic_housekeeper_dir, "XXXXXXXXX_000000_S000_L004_R1_001.fastq.gz"
    ).as_posix()
    with gzip.open(fastq_filename, "wb") as wh:
        wh.write(b"@A00689:73:XXXXXXXXX:4:1101:4806:1047 1:N:0:TCCTGGAACA+ACAACCAGTA")
    return fastq_filename


@pytest.fixture
def fastq_file_l_1_r_2(balsamic_housekeeper_dir: Path) -> str:
    fastq_filename = Path(
        balsamic_housekeeper_dir, "XXXXXXXXX_000000_S000_L001_R2_001.fastq.gz"
    ).as_posix()
    with gzip.open(fastq_filename, "wb") as wh:
        wh.write(b"@A00689:73:XXXXXXXXX:1:1101:4806:1047 2:N:0:TCCTGGAACA+ACAACCAGTA")
    return fastq_filename


@pytest.fixture
def fastq_file_l_2_r_2(balsamic_housekeeper_dir: Path) -> str:
    fastq_filename = Path(
        balsamic_housekeeper_dir, "XXXXXXXXX_000000_S000_L002_R2_001.fastq.gz"
    ).as_posix()
    with gzip.open(fastq_filename, "wb") as wh:
        wh.write(b"@A00689:73:XXXXXXXXX:2:1101:4806:1047 2:N:0:TCCTGGAACA+ACAACCAGTA")
    return fastq_filename


@pytest.fixture
def fastq_file_l_3_r_2(balsamic_housekeeper_dir: Path) -> str:
    fastq_filename = Path(
        balsamic_housekeeper_dir, "XXXXXXXXX_000000_S000_L003_R2_001.fastq.gz"
    ).as_posix()
    with gzip.open(fastq_filename, "wb") as wh:
        wh.write(b"@A00689:73:XXXXXXXXX:3:1101:4806:1047 2:N:0:TCCTGGAACA+ACAACCAGTA")
    return fastq_filename


@pytest.fixture
def fastq_file_l_4_r_2(balsamic_housekeeper_dir: Path) -> str:
    fastq_filename = Path(
        balsamic_housekeeper_dir, "XXXXXXXXX_000000_S000_L004_R2_001.fastq.gz"
    ).as_posix()
    with gzip.open(fastq_filename, "wb") as wh:
        wh.write(b"@A00689:73:XXXXXXXXX:4:1101:4806:1047 2:N:0:TCCTGGAACA+ACAACCAGTA")
    return fastq_filename


@pytest.fixture
def balsamic_mock_fastq_files(
    fastq_file_l_1_r_1: Path,
    fastq_file_l_1_r_2: Path,
    fastq_file_l_2_r_1: Path,
    fastq_file_l_2_r_2: Path,
    fastq_file_l_3_r_1: Path,
    fastq_file_l_3_r_2: Path,
    fastq_file_l_4_r_1: Path,
    fastq_file_l_4_r_2: Path,
) -> list:
    """Return list of all mock fastq files to commmit to mock housekeeper"""
    return [
        fastq_file_l_1_r_1,
        fastq_file_l_1_r_2,
        fastq_file_l_2_r_1,
        fastq_file_l_2_r_2,
        fastq_file_l_3_r_1,
        fastq_file_l_3_r_2,
        fastq_file_l_4_r_1,
        fastq_file_l_4_r_2,
    ]


@pytest.fixture(scope="function")
def balsamic_housekeeper(housekeeper_api, helpers, balsamic_mock_fastq_files: list):
    """Create populated housekeeper that holds files for all mock samples"""

    samples = [
        "sample_case_wgs_paired_tumor",
        "sample_case_wgs_paired_normal",
        "sample_case_tgs_paired_tumor",
        "sample_case_tgs_paired_normal",
        "sample_case_wgs_single_tumor",
        "sample_case_tgs_single_tumor",
        "sample_case_tgs_single_normal_error",
        "sample_case_tgs_paired_tumor_error",
        "sample_case_tgs_paired_tumor2_error",
        "sample_case_tgs_paired_normal_error",
        "mixed_sample_case_wgs_paired_tumor_error",
        "mixed_sample_case_tgs_paired_normal_error",
        "mixed_sample_case_mixed_bed_paired_tumor_error",
        "mixed_sample_case_mixed_bed_paired_normal_error",
        "mip_sample_case_wgs_single_tumor",
        "sample_case_wgs_paired_two_normal_tumor_error",
        "sample_case_wgs_paired_two_normal_normal1_error",
        "sample_case_wgs_paired_two_normal_normal2_error",
        "sample_case_wes_panel_error",
        "sample_case_wes_tumor",
    ]

    for sample in samples:
        bundle_data = {
            "name": sample,
            "created": dt.datetime.now(),
            "version": "1.0",
            "files": [
                {"path": f, "tags": [SequencingFileTag.FASTQ], "archive": False}
                for f in balsamic_mock_fastq_files
            ],
        }
        helpers.ensure_hk_bundle(store=housekeeper_api, bundle_data=bundle_data)
    return housekeeper_api


@pytest.fixture
def balsamic_lims(context_config: dict) -> MockLimsAPI:
    """Create populated mock LIMS api to mimic all functionality of LIMS used by BALSAMIC"""

    balsamic_lims = MockLimsAPI(context_config)
    balsamic_lims.add_capture_kit(
        internal_id="sample_case_wgs_paired_tumor",
        capture_kit=None,
    )
    balsamic_lims.add_capture_kit(
        internal_id="sample_case_wgs_paired_normal",
        capture_kit=None,
    )
    balsamic_lims.add_capture_kit(
        internal_id="sample_case_tgs_paired_tumor",
        capture_kit="BalsamicBed1",
    )
    balsamic_lims.add_capture_kit(
        internal_id="sample_case_tgs_paired_normal",
        capture_kit="BalsamicBed1",
    )
    balsamic_lims.add_capture_kit(
        internal_id="sample_case_wgs_single_tumor",
        capture_kit=None,
    )
    balsamic_lims.add_capture_kit(
        internal_id="sample_case_tgs_single_tumor",
        capture_kit="BalsamicBed1",
    )
    balsamic_lims.add_capture_kit(
        internal_id="sample_case_tgs_single_normal_error",
        capture_kit="BalsamicBed1",
    )
    balsamic_lims.add_capture_kit(
        internal_id="sample_case_tgs_paired_tumor_error",
        capture_kit="BalsamicBed1",
    )
    balsamic_lims.add_capture_kit(
        internal_id="sample_case_tgs_paired_tumor2_error",
        capture_kit="BalsamicBed1",
    )
    balsamic_lims.add_capture_kit(
        internal_id="sample_case_tgs_paired_normal_error",
        capture_kit="BalsamicBed1",
    )
    balsamic_lims.add_capture_kit(
        internal_id="mixed_sample_case_wgs_paired_tumor_error",
        capture_kit=None,
    )
    balsamic_lims.add_capture_kit(
        internal_id="mixed_sample_case_tgs_paired_normal_error",
        capture_kit="BalsamicBed1",
    )
    balsamic_lims.add_capture_kit(
        internal_id="mixed_sample_case_mixed_bed_paired_tumor_error",
        capture_kit="BalsamicBed1",
    )
    balsamic_lims.add_capture_kit(
        internal_id="mixed_sample_case_mixed_bed_paired_normal_error",
        capture_kit="BalsamicBed2",
    )
    balsamic_lims.add_capture_kit(
        internal_id="sample_case_wes_tumor",
        capture_kit="BalsamicBed2",
    )

    balsamic_lims.add_capture_kit(
        internal_id="mip_sample_case_wgs_single_tumor",
        capture_kit=None,
    )
    balsamic_lims.add_capture_kit(
        internal_id="sample_case_wgs_paired_two_normal_tumor_error",
        capture_kit=None,
    )
    balsamic_lims.add_capture_kit(
        internal_id="sample_case_wgs_paired_two_normal_normal1_error",
        capture_kit=None,
    )
    balsamic_lims.add_capture_kit(
        internal_id="sample_case_wgs_paired_two_normal_normal2_error",
        capture_kit=None,
    )

    return balsamic_lims


@pytest.fixture(scope="function")
def balsamic_context(
    cg_context: CGConfig,
    helpers: StoreHelpers,
    balsamic_lims: MockLimsAPI,
    balsamic_housekeeper: HousekeeperAPI,
    trailblazer_api: MockTB,
    cg_dir,
) -> CGConfig:
    """context to use in cli"""
    cg_context.housekeeper_api_ = balsamic_housekeeper
    cg_context.lims_api_ = balsamic_lims
    cg_context.trailblazer_api_ = trailblazer_api
    cg_context.meta_apis["analysis_api"] = BalsamicAnalysisAPI(config=cg_context)
    status_db: Store = cg_context.status_db

    # Create tgs application version
    helpers.ensure_application_version(
        store=status_db,
        application_tag="TGSA",
        prep_category=PrepCategory.TARGETED_GENOME_SEQUENCING,
        target_reads=10,
    )

    # Create wes application version
    helpers.ensure_application_version(
        store=status_db,
        application_tag="WESA",
        prep_category=PrepCategory.WHOLE_EXOME_SEQUENCING,
        target_reads=10,
    )

    # Create wgs application version
    helpers.ensure_application_version(
        store=status_db,
        application_tag="WGSA",
        prep_category=PrepCategory.WHOLE_GENOME_SEQUENCING,
        target_reads=10,
    )

    # Create a mic application version
    helpers.ensure_application_version(
        store=status_db,
        application_tag="MICA",
        prep_category="mic",
        target_reads=10,
    )

    # Create textbook case for WGS PAIRED with enough reads
    case_wgs_paired_enough_reads = helpers.add_case(
        store=status_db,
        internal_id="balsamic_case_wgs_paired_enough_reads",
        name="balsamic_case_wgs_paired_enough_reads",
        data_analysis=Workflow.BALSAMIC,
        action=CaseActions.HOLD,
    )
    sample_case_wgs_paired_tumor_enough_reads = helpers.add_sample(
        status_db,
        application_type=PrepCategory.WHOLE_GENOME_SEQUENCING,
        is_tumour=True,
        internal_id="sample_case_wgs_paired_tumor_enough_reads",
        reads=10,
        last_sequenced_at=dt.datetime.now(),
    )
    sample_case_wgs_paired_normal_enough_reads = helpers.add_sample(
        status_db,
        application_type=PrepCategory.WHOLE_GENOME_SEQUENCING,
        is_tumour=False,
        internal_id="sample_case_wgs_paired_normal_enough_reads",
        reads=10,
        last_sequenced_at=dt.datetime.now(),
    )
    helpers.add_relationship(
        status_db,
        case=case_wgs_paired_enough_reads,
        sample=sample_case_wgs_paired_tumor_enough_reads,
    )
    helpers.add_relationship(
        status_db,
        case=case_wgs_paired_enough_reads,
        sample=sample_case_wgs_paired_normal_enough_reads,
    )

    # Create textbook case for WGS PAIRED
    case_wgs_paired = helpers.add_case(
        store=status_db,
        internal_id="balsamic_case_wgs_paired",
        name="balsamic_case_wgs_paired",
        data_analysis=Workflow.BALSAMIC,
        action=CaseActions.HOLD,
    )
    sample_case_wgs_paired_tumor = helpers.add_sample(
        status_db,
        application_type=PrepCategory.WHOLE_GENOME_SEQUENCING,
        is_tumour=True,
        internal_id="sample_case_wgs_paired_tumor",
        reads=10,
        last_sequenced_at=dt.datetime.now(),
    )
    sample_case_wgs_paired_normal = helpers.add_sample(
        status_db,
        application_type=PrepCategory.WHOLE_GENOME_SEQUENCING,
        is_tumour=False,
        internal_id="sample_case_wgs_paired_normal",
        reads=10,
        last_sequenced_at=dt.datetime.now(),
    )
    helpers.add_relationship(status_db, case=case_wgs_paired, sample=sample_case_wgs_paired_tumor)
    helpers.add_relationship(status_db, case=case_wgs_paired, sample=sample_case_wgs_paired_normal)

    # Create textbook case for TGS PAIRED without enough reads
    case_tgs_paired = helpers.add_case(
        status_db,
        internal_id="balsamic_case_tgs_paired",
        name="balsamic_case_tgs_paired",
        data_analysis=Workflow.BALSAMIC,
    )
    sample_case_tgs_paired_tumor = helpers.add_sample(
        status_db,
        application_tag="TGSA",
        application_type=PrepCategory.TARGETED_GENOME_SEQUENCING,
        is_tumour=True,
        internal_id="sample_case_tgs_paired_tumor",
        reads=10,
        last_sequenced_at=dt.datetime.now(),
    )
    sample_case_tgs_paired_normal = helpers.add_sample(
        status_db,
        application_tag="TGSA",
        application_type=PrepCategory.TARGETED_GENOME_SEQUENCING,
        is_tumour=False,
        internal_id="sample_case_tgs_paired_normal",
        reads=0,
        last_sequenced_at=dt.datetime.now(),
    )
    helpers.add_relationship(status_db, case=case_tgs_paired, sample=sample_case_tgs_paired_tumor)
    helpers.add_relationship(status_db, case=case_tgs_paired, sample=sample_case_tgs_paired_normal)

    # Create textbook case for WGS TUMOR ONLY
    case_wgs_single = helpers.add_case(
        status_db,
        internal_id="balsamic_case_wgs_single",
        name="balsamic_case_wgs_single",
        data_analysis=Workflow.BALSAMIC,
    )
    sample_case_wgs_single_tumor = helpers.add_sample(
        status_db,
        application_type=PrepCategory.WHOLE_GENOME_SEQUENCING,
        is_tumour=True,
        internal_id="sample_case_wgs_single_tumor",
        reads=100,
        last_sequenced_at=dt.datetime.now(),
    )
    helpers.add_relationship(status_db, case=case_wgs_single, sample=sample_case_wgs_single_tumor)

    # Create textbook case for TGS TUMOR ONLY
    case_tgs_single = helpers.add_case(
        status_db,
        internal_id="balsamic_case_tgs_single",
        name="balsamic_case_tgs_single",
        data_analysis=Workflow.BALSAMIC,
    )
    sample_case_tgs_single_tumor = helpers.add_sample(
        status_db,
        application_tag="TGSA",
        application_type=PrepCategory.TARGETED_GENOME_SEQUENCING,
        is_tumour=True,
        internal_id="sample_case_tgs_single_tumor",
        last_sequenced_at=dt.datetime.now(),
    )
    helpers.add_relationship(status_db, case=case_tgs_single, sample=sample_case_tgs_single_tumor)

    # Create ERROR case for TGS NORMAL ONLY
    case_tgs_single_error = helpers.add_case(
        status_db,
        internal_id="balsamic_case_tgs_single_error",
        name="balsamic_case_tgs_single_error",
        data_analysis=Workflow.BALSAMIC,
    )
    sample_case_tgs_single_normal_error = helpers.add_sample(
        status_db,
        application_tag="TGSA",
        application_type=PrepCategory.TARGETED_GENOME_SEQUENCING,
        is_tumour=False,
        internal_id="sample_case_tgs_single_normal_error",
        reads=0,
        last_sequenced_at=dt.datetime.now(),
    )
    helpers.add_relationship(
        status_db,
        case=case_tgs_single_error,
        sample=sample_case_tgs_single_normal_error,
    )

    # Create ERROR case for TGS TWO TUMOR ONE NORMAL
    case_tgs_paired_error = helpers.add_case(
        status_db,
        internal_id="balsamic_case_tgs_paired_error",
        name="balsamic_case_tgs_paired_error",
        data_analysis=Workflow.BALSAMIC,
    )
    sample_case_tgs_paired_tumor_error = helpers.add_sample(
        status_db,
        application_tag="TGSA",
        application_type=PrepCategory.TARGETED_GENOME_SEQUENCING,
        is_tumour=True,
        reads=0,
        internal_id="sample_case_tgs_paired_tumor_error",
        last_sequenced_at=dt.datetime.now(),
    )
    sample_case_tgs_paired_tumor2_error = helpers.add_sample(
        status_db,
        application_tag="TGSA",
        application_type=PrepCategory.TARGETED_GENOME_SEQUENCING,
        is_tumour=True,
        reads=0,
        internal_id="sample_case_tgs_paired_tumor2_error",
        last_sequenced_at=dt.datetime.now(),
    )
    sample_case_tgs_paired_normal_error = helpers.add_sample(
        status_db,
        application_tag="TGSA",
        application_type=PrepCategory.TARGETED_GENOME_SEQUENCING,
        is_tumour=False,
        reads=0,
        internal_id="sample_case_tgs_paired_normal_error",
        last_sequenced_at=dt.datetime.now(),
    )
    helpers.add_relationship(
        status_db,
        case=case_tgs_paired_error,
        sample=sample_case_tgs_paired_tumor_error,
    )
    helpers.add_relationship(
        status_db,
        case=case_tgs_paired_error,
        sample=sample_case_tgs_paired_tumor2_error,
    )
    helpers.add_relationship(
        status_db,
        case=case_tgs_paired_error,
        sample=sample_case_tgs_paired_normal_error,
    )

    # Create ERROR case for MIXED application type
    case_mixed_paired_error = helpers.add_case(
        status_db,
        internal_id="balsamic_case_mixed_paired_error",
        name="balsamic_case_mixed_paired_error",
        data_analysis=Workflow.BALSAMIC,
    )
    mixed_sample_case_wgs_paired_tumor_error = helpers.add_sample(
        status_db,
        application_type=PrepCategory.WHOLE_GENOME_SEQUENCING,
        is_tumour=True,
        reads=0,
        internal_id="mixed_sample_case_wgs_paired_tumor_error",
        last_sequenced_at=dt.datetime.now(),
    )
    mixed_sample_case_tgs_paired_normal_error = helpers.add_sample(
        status_db,
        application_tag="TGSA",
        application_type=PrepCategory.TARGETED_GENOME_SEQUENCING,
        is_tumour=False,
        reads=0,
        internal_id="mixed_sample_case_tgs_paired_normal_error",
        last_sequenced_at=dt.datetime.now(),
    )
    helpers.add_relationship(
        status_db,
        case=case_mixed_paired_error,
        sample=mixed_sample_case_wgs_paired_tumor_error,
    )
    helpers.add_relationship(
        status_db,
        case=case_mixed_paired_error,
        sample=mixed_sample_case_tgs_paired_normal_error,
    )

    # Create ERROR case for MIXED application type NOT BALSAMIC APPLICATION
    case_mixed_wgs_mic_paired_error = helpers.add_case(
        status_db,
        internal_id="balsamic_case_mixed_wgs_mic_paired_error",
        name="balsamic_case_mixed_wgs_mic_paired_error",
        data_analysis=Workflow.BALSAMIC,
    )
    mixed_sample_case_wgs_mic_paired_tumor_error = helpers.add_sample(
        status_db,
        application_type=PrepCategory.WHOLE_GENOME_SEQUENCING,
        is_tumour=True,
        internal_id="mixed_sample_case_wgs_mic_paired_tumor_error",
        reads=0,
        last_sequenced_at=dt.datetime.now(),
    )
    mixed_sample_case_wgs_mic_paired_normal_error: Sample = helpers.add_sample(
        status_db,
        application_tag="MICA",
        application_type="mic",
        is_tumour=False,
        internal_id="mixed_sample_case_wgs_mic_paired_normal_error",
        reads=0,
        last_sequenced_at=dt.datetime.now(),
    )
    helpers.add_relationship(
        status_db,
        case=case_mixed_wgs_mic_paired_error,
        sample=mixed_sample_case_wgs_mic_paired_tumor_error,
    )
    helpers.add_relationship(
        status_db,
        case=case_mixed_wgs_mic_paired_error,
        sample=mixed_sample_case_wgs_mic_paired_normal_error,
    )

    # Create ERROR case for MIXED TARGET BED
    case_mixed_bed_paired_error = helpers.add_case(
        status_db,
        internal_id="balsamic_case_mixed_bed_paired_error",
        name="balsamic_case_mixed_bed_paired_error",
        data_analysis=Workflow.BALSAMIC,
    )
    mixed_sample_case_mixed_bed_paired_tumor_error = helpers.add_sample(
        status_db,
        application_tag="TGSA",
        application_type=PrepCategory.TARGETED_GENOME_SEQUENCING,
        is_tumour=True,
        internal_id="mixed_sample_case_mixed_bed_paired_tumor_error",
        last_sequenced_at=dt.datetime.now(),
    )
    mixed_sample_case_mixed_bed_paired_normal_error = helpers.add_sample(
        status_db,
        application_tag="TGSA",
        application_type=PrepCategory.TARGETED_GENOME_SEQUENCING,
        is_tumour=False,
        internal_id="mixed_sample_case_mixed_bed_paired_normal_error",
        reads=0,
        last_sequenced_at=dt.datetime.now(),
    )
    helpers.add_relationship(
        status_db,
        case=case_mixed_bed_paired_error,
        sample=mixed_sample_case_mixed_bed_paired_tumor_error,
    )
    helpers.add_relationship(
        status_db,
        case=case_mixed_bed_paired_error,
        sample=mixed_sample_case_mixed_bed_paired_normal_error,
    )

    # Create ERROR case for WGS TUMOR ONLY MIP CLI_OPTION_ANALYSIS ONLY
    mip_case_wgs_single = helpers.add_case(
        status_db,
        internal_id="mip_case_wgs_single",
        name="mip_case_wgs_single",
        data_analysis=Workflow.MIP_DNA,
    )
    mip_sample_case_wgs_single_tumor = helpers.add_sample(
        status_db,
        application_type=PrepCategory.WHOLE_GENOME_SEQUENCING,
        is_tumour=True,
        internal_id="mip_sample_case_wgs_single_tumor",
        last_sequenced_at=dt.datetime.now(),
    )
    helpers.add_relationship(
        status_db,
        case=mip_case_wgs_single,
        sample=mip_sample_case_wgs_single_tumor,
    )

    # Create ERROR case for WGS ONE TUMOR TWO NORMAL
    case_wgs_paired_two_normal_error = helpers.add_case(
        status_db,
        internal_id="balsamic_case_wgs_paired_two_normal_error",
        name="balsamic_case_wgs_paired_two_normal_error",
        data_analysis=Workflow.BALSAMIC,
    )
    sample_case_wgs_paired_two_normal_tumor_error = helpers.add_sample(
        status_db,
        application_tag="WGSA",
        application_type=PrepCategory.WHOLE_GENOME_SEQUENCING,
        is_tumour=True,
        internal_id="sample_case_wgs_paired_two_normal_tumor_error",
        reads=0,
        last_sequenced_at=dt.datetime.now(),
    )
    sample_case_wgs_paired_two_normal_normal1_error = helpers.add_sample(
        status_db,
        application_tag="WGSA",
        application_type=PrepCategory.WHOLE_GENOME_SEQUENCING,
        is_tumour=False,
        internal_id="sample_case_wgs_paired_two_normal_normal1_error",
        reads=0,
        last_sequenced_at=dt.datetime.now(),
    )
    sample_case_wgs_paired_two_normal_normal2_error = helpers.add_sample(
        status_db,
        application_tag="WGSA",
        application_type=PrepCategory.WHOLE_GENOME_SEQUENCING,
        is_tumour=False,
        internal_id="sample_case_wgs_paired_two_normal_normal2_error",
        reads=0,
        last_sequenced_at=dt.datetime.now(),
    )
    helpers.add_relationship(
        status_db,
        case=case_wgs_paired_two_normal_error,
        sample=sample_case_wgs_paired_two_normal_tumor_error,
    )
    helpers.add_relationship(
        status_db,
        case=case_wgs_paired_two_normal_error,
        sample=sample_case_wgs_paired_two_normal_normal1_error,
    )
    helpers.add_relationship(
        status_db,
        case=case_wgs_paired_two_normal_error,
        sample=sample_case_wgs_paired_two_normal_normal2_error,
    )

    # Create WES case with 1 tumor sample
    case_wes_tumor = helpers.add_case(
        status_db,
        internal_id="balsamic_case_wes_tumor",
        name="balsamic_case_wes_tumor",
        data_analysis=Workflow.BALSAMIC,
    )
    sample_case_wes_tumor = helpers.add_sample(
        status_db,
        application_tag="WESA",
        application_type=PrepCategory.WHOLE_EXOME_SEQUENCING,
        is_tumour=True,
        internal_id="sample_case_wes_tumor",
        last_sequenced_at=dt.datetime.now(),
    )
    helpers.add_relationship(status_db, case=case_wes_tumor, sample=sample_case_wes_tumor)

    # Create ERROR case for WES when no panel is found
    case_wes_panel_error = helpers.add_case(
        status_db,
        internal_id="balsamic_case_wes_panel_error",
        name="balsamic_case_wes_panel_error",
        data_analysis=Workflow.BALSAMIC,
    )
    sample_case_wes_panel_error = helpers.add_sample(
        status_db,
        application_tag="WESA",
        application_type=PrepCategory.WHOLE_EXOME_SEQUENCING,
        is_tumour=True,
        internal_id="sample_case_wes_panel_error",
        reads=0,
        last_sequenced_at=dt.datetime.now(),
    )
    helpers.add_relationship(
        status_db, case=case_wes_panel_error, sample=sample_case_wes_panel_error
    )

    # Create ERROR case with NO SAMPLES
    helpers.add_case(status_db, internal_id="no_sample_case", name="no_sample_case")

    # Create BED1 version 1
    bed1_name = "BalsamicBed1"
    bed1_filename = "balsamic_bed_1.bed"
    Path(cg_dir, bed1_filename).touch(exist_ok=True)
    bed1 = status_db.add_bed(name=bed1_name)
    status_db.session.add(bed1)
    version1 = status_db.add_bed_version(
        bed=bed1, version=1, filename=bed1_filename, shortname=bed1_name
    )
    status_db.session.add(version1)

    # Create BED2 version 1
    bed2_name = "BalsamicBed2"
    bed2_filename = "balsamic_bed_2.bed"
    Path(cg_dir, bed2_filename).touch(exist_ok=True)
    bed2 = status_db.add_bed(name=bed2_name)
    status_db.session.add(bed2)
    version2 = status_db.add_bed_version(
        bed=bed2, version=1, filename=bed2_filename, shortname=bed2_name
    )
    status_db.session.add(version2)
    status_db.session.commit()
    return cg_context


@pytest.fixture
def mock_config(balsamic_dir: Path, balsamic_case_id: str) -> None:
    """Create dummy config file at specified path"""

    config_data = {
        "analysis": {
            "case_id": f"{balsamic_case_id}",
            "analysis_type": "paired",
            "sequencing_type": "targeted",
            "analysis_dir": f"{balsamic_dir}",
            "fastq_path": f"{balsamic_dir}/{balsamic_case_id}/analysis/fastq/",
            "script": f"{balsamic_dir}/{balsamic_case_id}/scripts/",
            "log": f"{balsamic_dir}/{balsamic_case_id}/logs/",
            "result": f"{balsamic_dir}/{balsamic_case_id}/analysis",
            "benchmark": f"{balsamic_dir}/{balsamic_case_id}/benchmarks/",
            "dag": f"{balsamic_dir}/{balsamic_case_id}/{balsamic_case_id}_BALSAMIC_4.4.0_graph.pdf",
            "BALSAMIC_version": "4",
            "config_creation_date": "2020-07-15 17:35",
        }
    }
    Path.mkdir(Path(balsamic_dir, balsamic_case_id), parents=True, exist_ok=True)
    WriteFile.write_file_from_content(
        content=config_data,
        file_format=FileFormat.JSON,
        file_path=Path(balsamic_dir, balsamic_case_id, balsamic_case_id + ".json"),
    )


@pytest.fixture
def deliverable_data(balsamic_dir: Path, balsamic_case_id: str) -> dict:
    samples = [
        "sample_case_wgs_single_tumor",
    ]

    return {
        "files": [
            {
                "path": f"{balsamic_dir}/{balsamic_case_id}/multiqc_report.html",
                "path_index": "",
                "step": "multiqc",
                "tag": ["qc"],
                "id": "T_WGS",
                "format": "html",
                "mandatory": True,
            },
            {
                "path": f"{balsamic_dir}/{balsamic_case_id}/concatenated_{samples[0]}_R_1.fp.fastq.gz",
                "path_index": "",
                "step": "fastp",
                "tag": [f"concatenated_{samples[0]}_R", "qc"],
                "id": f"concatenated_{samples[0]}_R",
                "format": "fastq.gz",
                "mandatory": True,
            },
            {
                "path": f"{balsamic_dir}/{balsamic_case_id}/CNV.somatic.{balsamic_case_id}.cnvkit.pass.vcf.gz.tbi",
                "path_index": "",
                "step": "vep_somatic",
                "format": "vcf.gz.tbi",
                "tag": [
                    "CNV",
                    balsamic_case_id,
                    "cnvkit",
                    "annotation",
                    "somatic",
                    "index",
                ],
                "id": balsamic_case_id,
                "mandatory": True,
            },
        ]
    }


@pytest.fixture
def mock_deliverable(balsamic_dir: Path, deliverable_data: dict, balsamic_case_id: str) -> None:
    """Create deliverable file with dummy data and files to deliver"""
    Path.mkdir(
        Path(balsamic_dir, balsamic_case_id, "analysis", "delivery_report"),
        parents=True,
        exist_ok=True,
    )
    for report_entry in deliverable_data["files"]:
        Path(report_entry["path"]).touch(exist_ok=True)
    WriteFile.write_file_from_content(
        content=deliverable_data,
        file_format=FileFormat.JSON,
        file_path=Path(
            balsamic_dir, balsamic_case_id, "analysis", "delivery_report", balsamic_case_id + ".hk"
        ),
    )


@pytest.fixture
def hermes_deliverables(deliverable_data: dict, balsamic_case_id: str) -> dict:
    hermes_output: dict = {"workflow": "balsamic", "bundle_id": balsamic_case_id, "files": []}
    for file_info in deliverable_data["files"]:
        tags: list[str] = []
        if "html" in file_info["format"]:
            tags.append("multiqc-html")
        elif "fastq" in file_info["format"]:
            tags.append("fastq")
        elif "vcf" in file_info["format"]:
            tags.extend(["vcf-snv-clinical", "cnvkit", "filtered"])
        hermes_output["files"].append({"path": file_info["path"], "tags": tags, "mandatory": True})
    return hermes_output


@pytest.fixture
def malformed_hermes_deliverables(hermes_deliverables: dict) -> dict:
    malformed_deliverable = hermes_deliverables.copy()
    malformed_deliverable.pop("workflow")

    return malformed_deliverable


@pytest.fixture
def mock_analysis_finish(balsamic_dir: Path, balsamic_case_id: str) -> None:
    """Create analysis_finish file for testing"""
    Path.mkdir(Path(balsamic_dir, balsamic_case_id, "analysis"), parents=True, exist_ok=True)
    Path(balsamic_dir, balsamic_case_id, "analysis", "analysis_finish").touch(exist_ok=True)
