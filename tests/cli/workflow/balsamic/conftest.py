"""Fixtures for cli workflow balsamic tests"""

import datetime as dt
import gzip
import json
from pathlib import Path
from typing import List

import pytest
from cg.apps.balsamic.api import BalsamicAPI
from cg.apps.balsamic.fastq import FastqHandler
from cg.apps.hermes.hermes_api import HermesApi
from cg.apps.housekeeper.hk import HousekeeperAPI
from cg.constants import Pipeline
from cg.meta.workflow.balsamic import BalsamicAnalysisAPI
from cg.store import Store
from tests.mocks.limsmock import MockLimsAPI
from tests.mocks.process_mock import ProcessMock


@pytest.fixture(name="balsamic_dir")
def balsamic_dir(tmpdir_factory, apps_dir: Path) -> Path:
    """Return the path to the balsamic apps dir"""
    balsamic_dir = tmpdir_factory.mktemp("balsamic")
    return Path(balsamic_dir).absolute().as_posix()


@pytest.fixture(name="balsamic_housekeeper_dir")
def balsamic_housekeeeper_dir(tmpdir_factory, balsamic_dir: Path) -> Path:
    """Return the path to the balsamic housekeeper dir"""
    balsamic_housekeeper_dir = tmpdir_factory.mktemp("bundles")
    return balsamic_housekeeper_dir


@pytest.fixture(name="balsamic_singularity_path")
def balsamic_singularity_path(balsamic_dir: Path) -> Path:
    balsamic_singularity_path = Path(balsamic_dir, "singularity.sif")
    balsamic_singularity_path.touch(exist_ok=True)
    return balsamic_singularity_path.as_posix()


@pytest.fixture(name="balsamic_reference_path")
def balsamic_reference_path(balsamic_dir: Path) -> Path:
    balsamic_reference_path = Path(balsamic_dir, "reference.json")
    balsamic_reference_path.touch(exist_ok=True)
    return balsamic_reference_path.as_posix()


@pytest.fixture(name="balsamic_bed_1_path")
def balsamic_bed_1_path(balsamic_dir: Path) -> Path:
    balsamic_bed_1_path = Path(balsamic_dir, "balsamic_bed_1.bed")
    balsamic_bed_1_path.touch(exist_ok=True)
    return balsamic_bed_1_path.as_posix()


@pytest.fixture(name="balsamic_bed_2_path")
def balsamic_bed_2_path(balsamic_dir: Path) -> Path:
    balsamic_bed_2_path = Path(balsamic_dir, "balsamic_bed_2.bed")
    balsamic_bed_2_path.touch(exist_ok=True)
    return balsamic_bed_2_path.as_posix()


@pytest.fixture
def fastq_file_l_1_r_1(balsamic_housekeeper_dir: Path) -> Path:
    fastq_filename = Path(
        balsamic_housekeeper_dir, "XXXXXXXXX_000000_S000_L001_R1_001.fastq.gz"
    ).as_posix()
    with gzip.open(fastq_filename, "wb") as wh:
        wh.write(b"@A00689:73:XXXXXXXXX:1:1101:4806:1047 1:N:0:TCCTGGAACA+ACAACCAGTA")
    return fastq_filename


@pytest.fixture
def fastq_file_l_2_r_1(balsamic_housekeeper_dir: Path) -> Path:
    fastq_filename = Path(
        balsamic_housekeeper_dir, "XXXXXXXXX_000000_S000_L002_R1_001.fastq.gz"
    ).as_posix()
    with gzip.open(fastq_filename, "wb") as wh:
        wh.write(b"@A00689:73:XXXXXXXXX:2:1101:4806:1047 1:N:0:TCCTGGAACA+ACAACCAGTA")
    return fastq_filename


@pytest.fixture
def fastq_file_l_3_r_1(balsamic_housekeeper_dir: Path) -> Path:
    fastq_filename = Path(
        balsamic_housekeeper_dir, "XXXXXXXXX_000000_S000_L003_R1_001.fastq.gz"
    ).as_posix()
    with gzip.open(fastq_filename, "wb") as wh:
        wh.write(b"@A00689:73:XXXXXXXXX:3:1101:4806:1047 1:N:0:TCCTGGAACA+ACAACCAGTA")
    return fastq_filename


@pytest.fixture
def fastq_file_l_4_r_1(balsamic_housekeeper_dir: Path) -> Path:
    fastq_filename = Path(
        balsamic_housekeeper_dir, "XXXXXXXXX_000000_S000_L004_R1_001.fastq.gz"
    ).as_posix()
    with gzip.open(fastq_filename, "wb") as wh:
        wh.write(b"@A00689:73:XXXXXXXXX:4:1101:4806:1047 1:N:0:TCCTGGAACA+ACAACCAGTA")
    return fastq_filename


@pytest.fixture
def fastq_file_l_1_r_2(balsamic_housekeeper_dir: Path) -> Path:
    fastq_filename = Path(
        balsamic_housekeeper_dir, "XXXXXXXXX_000000_S000_L001_R2_001.fastq.gz"
    ).as_posix()
    with gzip.open(fastq_filename, "wb") as wh:
        wh.write(b"@A00689:73:XXXXXXXXX:1:1101:4806:1047 2:N:0:TCCTGGAACA+ACAACCAGTA")
    return fastq_filename


@pytest.fixture
def fastq_file_l_2_r_2(balsamic_housekeeper_dir: Path) -> Path:
    fastq_filename = Path(
        balsamic_housekeeper_dir, "XXXXXXXXX_000000_S000_L002_R2_001.fastq.gz"
    ).as_posix()
    with gzip.open(fastq_filename, "wb") as wh:
        wh.write(b"@A00689:73:XXXXXXXXX:2:1101:4806:1047 2:N:0:TCCTGGAACA+ACAACCAGTA")
    return fastq_filename


@pytest.fixture
def fastq_file_l_3_r_2(balsamic_housekeeper_dir: Path) -> Path:
    fastq_filename = Path(
        balsamic_housekeeper_dir, "XXXXXXXXX_000000_S000_L003_R2_001.fastq.gz"
    ).as_posix()
    with gzip.open(fastq_filename, "wb") as wh:
        wh.write(b"@A00689:73:XXXXXXXXX:3:1101:4806:1047 2:N:0:TCCTGGAACA+ACAACCAGTA")
    return fastq_filename


@pytest.fixture
def fastq_file_l_4_r_2(balsamic_housekeeper_dir: Path) -> Path:
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


@pytest.fixture(scope="function", name="balsamic_housekeeper")
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
                {"path": f, "tags": ["fastq"], "archive": False} for f in balsamic_mock_fastq_files
            ],
        }
        helpers.ensure_hk_bundle(store=housekeeper_api, bundle_data=bundle_data)
    return housekeeper_api


@pytest.fixture
def server_config(
    balsamic_dir: Path,
    balsamic_housekeeper_dir: Path,
    balsamic_singularity_path: Path,
    balsamic_reference_path: Path,
) -> dict:
    """Mimic a dict normally found in cg context"""

    return {
        "database": "database",
        "bed_path": balsamic_dir,
        "balsamic": {
            "root": balsamic_dir,
            "singularity": Path(balsamic_dir, "singularity.sif").as_posix(),
            "reference_config": Path(balsamic_dir, "reference.json").as_posix(),
            "binary_path": "/home/proj/bin/conda/envs/S_BALSAMIC/bin/balsamic",
            "conda_env": "S_BALSAMIC",
            "slurm": {
                "mail_user": "test.mail@scilifelab.se",
                "account": "development",
                "qos": "low",
            },
        },
        "housekeeper": {
            "database": "database",
            "root": balsamic_housekeeper_dir,
        },
        "lims": {
            "host": "example.db",
            "username": "testuser",
            "password": "testpassword",
        },
    }


@pytest.fixture(name="balsamic_lims")
def balsamic_lims(server_config: dict) -> MockLimsAPI:
    """Create populated mock LIMS api to mimic all functionality of LIMS used by BALSAMIC"""

    balsamic_lims = MockLimsAPI(server_config)
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


@pytest.fixture(name="balsamic_store")
def balsamic_store(base_store: Store, balsamic_dir: Path, helpers) -> Store:
    """real store to be used in tests"""
    _store = base_store

    # Create tgs application version
    helpers.ensure_application_version(store=_store, application_tag="TGSA", application_type="tgs")

    # Create wes application version
    helpers.ensure_application_version(store=_store, application_tag="WESA", application_type="wes")

    # Create textbook case for WGS PAIRED with enough reads
    case_wgs_paired_enough_reads = helpers.add_case(
        store=_store,
        internal_id="balsamic_case_wgs_paired_enough_reads",
        case_id="balsamic_case_wgs_paired_enough_reads",
        data_analysis=Pipeline.BALSAMIC,
    )
    sample_case_wgs_paired_tumor_enough_reads = helpers.add_sample(
        _store,
        internal_id="sample_case_wgs_paired_tumor_enough_reads",
        is_tumour=True,
        application_type="wgs",
        reads=10,
        sequenced_at=dt.datetime.now(),
    )
    sample_case_wgs_paired_normal_enough_reads = helpers.add_sample(
        _store,
        internal_id="sample_case_wgs_paired_normal_enough_reads",
        is_tumour=False,
        application_type="wgs",
        reads=10,
        sequenced_at=dt.datetime.now(),
    )
    helpers.add_relationship(
        _store,
        case=case_wgs_paired_enough_reads,
        sample=sample_case_wgs_paired_tumor_enough_reads,
    )
    helpers.add_relationship(
        _store,
        case=case_wgs_paired_enough_reads,
        sample=sample_case_wgs_paired_normal_enough_reads,
    )

    # Create textbook case for WGS PAIRED
    case_wgs_paired = helpers.add_case(
        store=_store,
        internal_id="balsamic_case_wgs_paired",
        case_id="balsamic_case_wgs_paired",
        data_analysis=Pipeline.BALSAMIC,
    )
    sample_case_wgs_paired_tumor = helpers.add_sample(
        _store,
        internal_id="sample_case_wgs_paired_tumor",
        is_tumour=True,
        application_type="wgs",
        reads=10,
        sequenced_at=dt.datetime.now(),
    )
    sample_case_wgs_paired_normal = helpers.add_sample(
        _store,
        internal_id="sample_case_wgs_paired_normal",
        is_tumour=False,
        application_type="wgs",
        reads=10,
        sequenced_at=dt.datetime.now(),
    )
    helpers.add_relationship(_store, case=case_wgs_paired, sample=sample_case_wgs_paired_tumor)
    helpers.add_relationship(_store, case=case_wgs_paired, sample=sample_case_wgs_paired_normal)

    # Create textbook case for TGS PAIRED without enough reads
    case_tgs_paired = helpers.add_case(
        _store,
        internal_id="balsamic_case_tgs_paired",
        case_id="balsamic_case_tgs_paired",
        data_analysis=Pipeline.BALSAMIC,
    )
    sample_case_tgs_paired_tumor = helpers.add_sample(
        _store,
        internal_id="sample_case_tgs_paired_tumor",
        is_tumour=True,
        application_tag="TGSA",
        application_type="tgs",
        reads=10,
        data_analysis=Pipeline.BALSAMIC,
        sequenced_at=dt.datetime.now(),
    )
    sample_case_tgs_paired_normal = helpers.add_sample(
        _store,
        internal_id="sample_case_tgs_paired_normal",
        is_tumour=False,
        application_tag="TGSA",
        application_type="tgs",
        reads=0,
        sequenced_at=dt.datetime.now(),
    )
    helpers.add_relationship(_store, case=case_tgs_paired, sample=sample_case_tgs_paired_tumor)
    helpers.add_relationship(_store, case=case_tgs_paired, sample=sample_case_tgs_paired_normal)

    # Create textbook case for WGS TUMOR ONLY
    case_wgs_single = helpers.add_case(
        _store,
        internal_id="balsamic_case_wgs_single",
        case_id="balsamic_case_wgs_single",
        data_analysis=Pipeline.BALSAMIC,
    )
    sample_case_wgs_single_tumor = helpers.add_sample(
        _store,
        internal_id="sample_case_wgs_single_tumor",
        is_tumour=True,
        application_type="wgs",
        reads=100,
        sequenced_at=dt.datetime.now(),
    )
    helpers.add_relationship(_store, case=case_wgs_single, sample=sample_case_wgs_single_tumor)

    # Create textbook case for TGS TUMOR ONLY
    case_tgs_single = helpers.add_case(
        _store,
        internal_id="balsamic_case_tgs_single",
        case_id="balsamic_case_tgs_single",
        data_analysis=Pipeline.BALSAMIC,
    )
    sample_case_tgs_single_tumor = helpers.add_sample(
        _store,
        internal_id="sample_case_tgs_single_tumor",
        is_tumour=True,
        application_tag="TGSA",
        application_type="tgs",
        sequenced_at=dt.datetime.now(),
    )
    helpers.add_relationship(_store, case=case_tgs_single, sample=sample_case_tgs_single_tumor)

    # Create ERROR case for TGS NORMAL ONLY
    case_tgs_single_error = helpers.add_case(
        _store,
        internal_id="balsamic_case_tgs_single_error",
        case_id="balsamic_case_tgs_single_error",
        data_analysis=Pipeline.BALSAMIC,
    )
    sample_case_tgs_single_normal_error = helpers.add_sample(
        _store,
        internal_id="sample_case_tgs_single_normal_error",
        is_tumour=False,
        application_tag="TGSA",
        application_type="tgs",
        sequenced_at=dt.datetime.now(),
    )
    helpers.add_relationship(
        _store,
        case=case_tgs_single_error,
        sample=sample_case_tgs_single_normal_error,
    )

    # Create ERROR case for TGS TWO TUMOR ONE NORMAL
    case_tgs_paired_error = helpers.add_case(
        _store,
        internal_id="balsamic_case_tgs_paired_error",
        case_id="balsamic_case_tgs_paired_error",
        data_analysis=Pipeline.BALSAMIC,
    )
    sample_case_tgs_paired_tumor_error = helpers.add_sample(
        _store,
        internal_id="sample_case_tgs_paired_tumor_error",
        is_tumour=True,
        application_tag="TGSA",
        application_type="tgs",
        sequenced_at=dt.datetime.now(),
    )
    sample_case_tgs_paired_tumor2_error = helpers.add_sample(
        _store,
        internal_id="sample_case_tgs_paired_tumor2_error",
        is_tumour=True,
        application_tag="TGSA",
        application_type="tgs",
        sequenced_at=dt.datetime.now(),
    )
    sample_case_tgs_paired_normal_error = helpers.add_sample(
        _store,
        internal_id="sample_case_tgs_paired_normal_error",
        is_tumour=False,
        application_tag="TGSA",
        application_type="tgs",
        sequenced_at=dt.datetime.now(),
    )
    helpers.add_relationship(
        _store,
        case=case_tgs_paired_error,
        sample=sample_case_tgs_paired_tumor_error,
    )
    helpers.add_relationship(
        _store,
        case=case_tgs_paired_error,
        sample=sample_case_tgs_paired_tumor2_error,
    )
    helpers.add_relationship(
        _store,
        case=case_tgs_paired_error,
        sample=sample_case_tgs_paired_normal_error,
    )

    # Create ERROR case for MIXED application type
    case_mixed_paired_error = helpers.add_case(
        _store,
        internal_id="balsamic_case_mixed_paired_error",
        case_id="balsamic_case_mixed_paired_error",
        data_analysis=Pipeline.BALSAMIC,
    )
    mixed_sample_case_wgs_paired_tumor_error = helpers.add_sample(
        _store,
        internal_id="mixed_sample_case_wgs_paired_tumor_error",
        is_tumour=True,
        application_type="wgs",
        sequenced_at=dt.datetime.now(),
    )
    mixed_sample_case_tgs_paired_normal_error = helpers.add_sample(
        _store,
        internal_id="mixed_sample_case_tgs_paired_normal_error",
        is_tumour=False,
        application_tag="TGSA",
        application_type="tgs",
        sequenced_at=dt.datetime.now(),
    )
    helpers.add_relationship(
        _store,
        case=case_mixed_paired_error,
        sample=mixed_sample_case_wgs_paired_tumor_error,
    )
    helpers.add_relationship(
        _store,
        case=case_mixed_paired_error,
        sample=mixed_sample_case_tgs_paired_normal_error,
    )

    # Create ERROR case for MIXED application type NOT BALSAMIC APPLICATION
    case_mixed_wgs_mic_paired_error = helpers.add_case(
        _store,
        internal_id="balsamic_case_mixed_wgs_mic_paired_error",
        case_id="balsamic_case_mixed_wgs_mic_paired_error",
        data_analysis=Pipeline.BALSAMIC,
    )
    mixed_sample_case_wgs_mic_paired_tumor_error = helpers.add_sample(
        _store,
        internal_id="mixed_sample_case_wgs_mic_paired_tumor_error",
        is_tumour=True,
        application_type="wgs",
        sequenced_at=dt.datetime.now(),
    )
    mixed_sample_case_wgs_mic_paired_normal_error = helpers.add_sample(
        _store,
        internal_id="mixed_sample_case_wgs_mic_paired_normal_error",
        is_tumour=False,
        application_tag="MICA",
        application_type="mic",
        sequenced_at=dt.datetime.now(),
    )
    helpers.add_relationship(
        _store,
        case=case_mixed_wgs_mic_paired_error,
        sample=mixed_sample_case_wgs_mic_paired_tumor_error,
    )
    helpers.add_relationship(
        _store,
        case=case_mixed_wgs_mic_paired_error,
        sample=mixed_sample_case_wgs_mic_paired_normal_error,
    )

    # Create ERROR case for MIXED TARGET BED
    case_mixed_bed_paired_error = helpers.add_case(
        _store,
        internal_id="balsamic_case_mixed_bed_paired_error",
        case_id="balsamic_case_mixed_bed_paired_error",
        data_analysis=Pipeline.BALSAMIC,
    )
    mixed_sample_case_mixed_bed_paired_tumor_error = helpers.add_sample(
        _store,
        internal_id="mixed_sample_case_mixed_bed_paired_tumor_error",
        is_tumour=True,
        application_tag="TGSA",
        application_type="tgs",
        sequenced_at=dt.datetime.now(),
    )
    mixed_sample_case_mixed_bed_paired_normal_error = helpers.add_sample(
        _store,
        internal_id="mixed_sample_case_mixed_bed_paired_normal_error",
        is_tumour=False,
        application_tag="TGSA",
        application_type="tgs",
        sequenced_at=dt.datetime.now(),
    )
    helpers.add_relationship(
        _store,
        case=case_mixed_bed_paired_error,
        sample=mixed_sample_case_mixed_bed_paired_tumor_error,
    )
    helpers.add_relationship(
        _store,
        case=case_mixed_bed_paired_error,
        sample=mixed_sample_case_mixed_bed_paired_normal_error,
    )

    # Create ERROR case for WGS TUMOR ONLY MIP CLI_OPTION_ANALYSIS ONLY
    mip_case_wgs_single = helpers.add_case(
        _store,
        internal_id="mip_case_wgs_single",
        case_id="mip_case_wgs_single",
        data_analysis=Pipeline.MIP_DNA,
    )
    mip_sample_case_wgs_single_tumor = helpers.add_sample(
        _store,
        internal_id="mip_sample_case_wgs_single_tumor",
        is_tumour=True,
        application_type="wgs",
        sequenced_at=dt.datetime.now(),
    )
    helpers.add_relationship(
        _store,
        case=mip_case_wgs_single,
        sample=mip_sample_case_wgs_single_tumor,
    )

    # Create ERROR case for WGS ONE TUMOR TWO NORMAL
    case_wgs_paired_two_normal_error = helpers.add_case(
        _store,
        internal_id="balsamic_case_wgs_paired_two_normal_error",
        case_id="balsamic_case_wgs_paired_two_normal_error",
        data_analysis=Pipeline.BALSAMIC,
    )
    sample_case_wgs_paired_two_normal_tumor_error = helpers.add_sample(
        _store,
        internal_id="sample_case_wgs_paired_two_normal_tumor_error",
        is_tumour=True,
        application_tag="WGSA",
        application_type="wgs",
        sequenced_at=dt.datetime.now(),
    )
    sample_case_wgs_paired_two_normal_normal1_error = helpers.add_sample(
        _store,
        internal_id="sample_case_wgs_paired_two_normal_normal1_error",
        is_tumour=False,
        application_tag="WGSA",
        application_type="wgs",
        sequenced_at=dt.datetime.now(),
    )
    sample_case_wgs_paired_two_normal_normal2_error = helpers.add_sample(
        _store,
        internal_id="sample_case_wgs_paired_two_normal_normal2_error",
        is_tumour=False,
        application_tag="WGSA",
        application_type="wgs",
        sequenced_at=dt.datetime.now(),
    )
    helpers.add_relationship(
        _store,
        case=case_wgs_paired_two_normal_error,
        sample=sample_case_wgs_paired_two_normal_tumor_error,
    )
    helpers.add_relationship(
        _store,
        case=case_wgs_paired_two_normal_error,
        sample=sample_case_wgs_paired_two_normal_normal1_error,
    )
    helpers.add_relationship(
        _store,
        case=case_wgs_paired_two_normal_error,
        sample=sample_case_wgs_paired_two_normal_normal2_error,
    )

    # Create WES case with 1 tumor sample
    case_wes_tumor = helpers.add_case(
        _store,
        internal_id="balsamic_case_wes_tumor",
        case_id="balsamic_case_wes_tumor",
        data_analysis=Pipeline.BALSAMIC,
    )
    sample_case_wes_tumor = helpers.add_sample(
        _store,
        internal_id="sample_case_wes_tumor",
        is_tumour=True,
        application_tag="WESA",
        application_type="wes",
        sequenced_at=dt.datetime.now(),
    )
    helpers.add_relationship(_store, case=case_wes_tumor, sample=sample_case_wes_tumor)

    # Create ERROR case for WES when no panel is found
    case_wes_panel_error = helpers.add_case(
        _store,
        internal_id="balsamic_case_wes_panel_error",
        case_id="balsamic_case_wes_panel_error",
        data_analysis=Pipeline.BALSAMIC,
    )
    sample_case_wes_panel_error = helpers.add_sample(
        _store,
        internal_id="sample_case_wes_panel_error",
        is_tumour=True,
        application_tag="WESA",
        application_type="wes",
        sequenced_at=dt.datetime.now(),
    )
    helpers.add_relationship(_store, case=case_wes_panel_error, sample=sample_case_wes_panel_error)

    # Create ERROR case with NO SAMPLES
    helpers.add_case(_store, internal_id="no_sample_case", case_id="no_sample_case")

    # Create BED1 version 1
    bed1_name = "BalsamicBed1"
    bed1_filename = "balsamic_bed_1.bed"
    Path(balsamic_dir, bed1_filename).touch(exist_ok=True)
    bed1 = _store.add_bed(name=bed1_name)
    _store.add_commit(bed1)
    version1 = _store.add_bed_version(
        bed=bed1, version=1, filename=bed1_filename, shortname=bed1_name
    )
    _store.add_commit(version1)

    # Create BED2 version 1
    bed2_name = "BalsamicBed2"
    bed2_filename = "balsamic_bed_2.bed"
    Path(balsamic_dir, bed2_filename).touch(exist_ok=True)
    bed2 = _store.add_bed(name=bed2_name)
    _store.add_commit(bed2)
    version2 = _store.add_bed_version(
        bed=bed2, version=1, filename=bed2_filename, shortname=bed2_name
    )
    _store.add_commit(version2)

    return _store


@pytest.fixture(scope="function", name="balsamic_context")
def balsamic_context(
    server_config: dict,
    balsamic_store: Store,
    balsamic_lims: MockLimsAPI,
    balsamic_housekeeper: HousekeeperAPI,
    hermes_api: HermesApi,
    balsamic_hermes_process: ProcessMock,
    trailblazer_api,
) -> dict:
    """context to use in cli"""
    hermes_api.process = balsamic_hermes_process
    balsamic_analysis_api = BalsamicAnalysisAPI(
        balsamic_api=BalsamicAPI(server_config),
        store=balsamic_store,
        housekeeper_api=balsamic_housekeeper,
        fastq_handler=FastqHandler(server_config),
        lims_api=balsamic_lims,
        trailblazer_api=trailblazer_api,
        hermes_api=hermes_api,
    )
    return {
        "BalsamicAnalysisAPI": balsamic_analysis_api,
    }


@pytest.fixture
def mock_config(balsamic_dir: Path) -> None:
    """Create dummy config file at specified path"""

    case_id = "balsamic_case_wgs_single"
    config_data = {
        "analysis": {
            "case_id": f"{case_id}",
            "analysis_type": "paired",
            "sequencing_type": "targeted",
            "analysis_dir": f"{balsamic_dir}",
            "fastq_path": f"{balsamic_dir}/{case_id}/analysis/fastq/",
            "script": f"{balsamic_dir}/{case_id}/scripts/",
            "log": f"{balsamic_dir}/{case_id}/logs/",
            "result": f"{balsamic_dir}/{case_id}/analysis",
            "benchmark": f"{balsamic_dir}/{case_id}/benchmarks/",
            "dag": f"{balsamic_dir}/{case_id}/{case_id}_BALSAMIC_4.4.0_graph.pdf",
            "BALSAMIC_version": "4",
            "config_creation_date": "2020-07-15 17:35",
        }
    }
    Path.mkdir(Path(balsamic_dir, case_id), parents=True, exist_ok=True)
    config_path = Path(balsamic_dir, case_id, case_id + ".json")
    json.dump(config_data, open(config_path, "w"))


@pytest.fixture(name="balsamic_case_id")
def fixture_balsamic_case_id() -> str:
    return "balsamic_case_wgs_single"


@pytest.fixture(name="deliverable_data")
def fixture_deliverables_data(balsamic_dir: Path, balsamic_case_id: str) -> dict:
    case_id = balsamic_case_id
    samples = [
        "sample_case_wgs_single_tumor",
    ]

    _deliverable_data = {
        "files": [
            {
                "path": f"{balsamic_dir}/{case_id}/multiqc_report.html",
                "path_index": "",
                "step": "multiqc",
                "tag": ["qc"],
                "id": "T_WGS",
                "format": "html",
            },
            {
                "path": f"{balsamic_dir}/{case_id}/concatenated_{samples[0]}_R_1.fp.fastq.gz",
                "path_index": "",
                "step": "fastp",
                "tag": [f"concatenated_{samples[0]}_R", "qc"],
                "id": f"concatenated_{samples[0]}_R",
                "format": "fastq.gz",
            },
            {
                "path": f"{balsamic_dir}/{case_id}/CNV.somatic.{case_id}.cnvkit.pass.vcf.gz.tbi",
                "path_index": "",
                "step": "vep_somatic",
                "format": "vcf.gz.tbi",
                "tag": ["CNV", case_id, "cnvkit", "annotation", "somatic", "index"],
                "id": case_id,
            },
        ]
    }
    return _deliverable_data


@pytest.fixture
def mock_deliverable(balsamic_dir: Path, deliverable_data: dict, balsamic_case_id: str) -> None:
    """Create deliverable file with dummy data and files to deliver"""
    case_id = balsamic_case_id

    Path.mkdir(
        Path(balsamic_dir, case_id, "analysis", "delivery_report"),
        parents=True,
        exist_ok=True,
    )
    for report_entry in deliverable_data["files"]:
        Path(report_entry["path"]).touch(exist_ok=True)
    hk_report_path = Path(balsamic_dir, case_id, "analysis", "delivery_report", case_id + ".hk")
    json.dump(deliverable_data, open(hk_report_path, "w"))


@pytest.fixture(name="hermes_deliverables")
def fixture_hermes_deliverables(deliverable_data: dict, balsamic_case_id: str) -> dict:
    hermes_output: dict = {"pipeline": "balsamic", "bundle_id": balsamic_case_id, "files": []}
    for file_info in deliverable_data["files"]:
        tags: List[str] = []
        if "html" in file_info["format"]:
            tags.append("multiqc-html")
        elif "fastq" in file_info["format"]:
            tags.append("fastq")
        elif "vcf" in file_info["format"]:
            tags.extend(["vcf-snv-clinical", "cnvkit", "filtered"])
        hermes_output["files"].append({"path": file_info["path"], "tags": tags})
    return hermes_output


@pytest.fixture(name="malformed_hermes_deliverables")
def fixture_malformed_hermes_deliverables(hermes_deliverables: dict) -> dict:
    hermes_deliverables.pop("pipeline")

    return hermes_deliverables


@pytest.fixture(name="balsamic_hermes_process")
def fixture_balsamic_hermes_process(hermes_deliverables: dict, process: ProcessMock) -> ProcessMock:
    """Return a process mock populated with some fluffy hermes output"""
    process.set_stdout(text=json.dumps(hermes_deliverables))
    return process


@pytest.fixture
def mock_analysis_finish(balsamic_dir: Path) -> None:
    """Create analysis_finish file for testing"""
    case_id = "balsamic_case_wgs_single"
    Path.mkdir(Path(balsamic_dir, case_id, "analysis"), parents=True, exist_ok=True)
    Path(balsamic_dir, case_id, "analysis", "analysis_finish").touch(exist_ok=True)
