"""Fixtures for cli balsamic tests"""

from pathlib import Path

import pytest
import datetime as dt

import gzip
from cg.apps.balsamic.api import BalsamicAPI
from cg.apps.balsamic.fastq import FastqHandler
from cg.utils.fastq import FastqAPI
from cg.meta.workflow.balsamic import BalsamicAnalysisAPI
from tests.mocks.hk_mock import MockHousekeeperAPI


class MockLimsAPI:
    """Mock LIMS API to simulate LIMS behavior in BALSAMIC"""

    def __init__(self, config=None):
        self.config = config
        self.sample_vars = {}

    def add_sample(self, internal_id: str):
        self.sample_vars[internal_id] = {}

    def add_capture_kit(self, internal_id: str, capture_kit):
        if not internal_id in self.sample_vars:
            self.add_sample(internal_id)
        self.sample_vars[internal_id]["capture_kit"] = capture_kit

    def capture_kit(self, internal_id: str):
        if internal_id in self.sample_vars:
            return self.sample_vars[internal_id].get("capture_kit")
        return None


@pytest.fixture(name="balsamic_dir")
def fixture_balsamic_dir(tmpdir_factory, apps_dir: Path) -> Path:
    """Return the path to the balsamic apps dir"""
    balsamic_dir = tmpdir_factory.mktemp("balsamic")
    return Path(balsamic_dir).absolute().as_posix()


@pytest.fixture(name="balsamic_housekeeper_dir")
def fixture_balsamic_housekeeeper_dir(tmpdir_factory, balsamic_dir: Path) -> Path:
    """Return the path to the balsamic housekeeper dir"""
    balsamic_housekeeper_dir = tmpdir_factory.mktemp("bundles")
    return balsamic_housekeeper_dir


@pytest.fixture(name="balsamic_singularity_path")
def fixture_balsamic_singularity_path(balsamic_dir) -> Path:
    balsamic_singularity_path = Path(balsamic_dir, "singularity.sif")
    balsamic_singularity_path.touch(exist_ok=True)
    return balsamic_singularity_path.as_posix()


@pytest.fixture(name="balsamic_reference_path")
def fixture_balsamic_reference_path(balsamic_dir) -> Path:
    balsamic_reference_path = Path(balsamic_dir, "reference.json")
    balsamic_reference_path.touch(exist_ok=True)
    return balsamic_reference_path.as_posix()


@pytest.fixture(name="balsamic_bed_1_path")
def fixture_balsamic_bed_1_path(balsamic_dir):
    balsamic_bed_1_path = Path(balsamic_dir, "balsamic_bed_1.bed")
    balsamic_bed_1_path.touch(exist_ok=True)
    return balsamic_bed_1_path.as_posix()


@pytest.fixture(name="balsamic_bed_2_path")
def fixture_balsamic_bed_2_path(balsamic_dir):
    balsamic_bed_2_path = Path(balsamic_dir, "balsamic_bed_2.bed")
    balsamic_bed_2_path.touch(exist_ok=True)
    return balsamic_bed_2_path.as_posix()


@pytest.fixture
def fastq_file_l_1_r_1(balsamic_housekeeper_dir):
    fastq_filename = Path(
        balsamic_housekeeper_dir, "XXXXXXXXX_000000_S000_L001_R1_001.fastq.gz"
    ).as_posix()
    with gzip.open(fastq_filename, "wb") as wh:
        wh.write(b"@A00689:73:XXXXXXXXX:1:1101:4806:1047 1:N:0:TCCTGGAACA+ACAACCAGTA")
    return fastq_filename


@pytest.fixture
def fastq_file_l_2_r_1(balsamic_housekeeper_dir):
    fastq_filename = Path(
        balsamic_housekeeper_dir, "XXXXXXXXX_000000_S000_L002_R1_001.fastq.gz"
    ).as_posix()
    with gzip.open(fastq_filename, "wb") as wh:
        wh.write(b"@A00689:73:XXXXXXXXX:2:1101:4806:1047 1:N:0:TCCTGGAACA+ACAACCAGTA")
    return fastq_filename


@pytest.fixture
def fastq_file_l_3_r_1(balsamic_housekeeper_dir):
    fastq_filename = Path(
        balsamic_housekeeper_dir, "XXXXXXXXX_000000_S000_L003_R1_001.fastq.gz"
    ).as_posix()
    with gzip.open(fastq_filename, "wb") as wh:
        wh.write(b"@A00689:73:XXXXXXXXX:3:1101:4806:1047 1:N:0:TCCTGGAACA+ACAACCAGTA")
    return fastq_filename


@pytest.fixture
def fastq_file_l_4_r_1(balsamic_housekeeper_dir):
    fastq_filename = Path(
        balsamic_housekeeper_dir, "XXXXXXXXX_000000_S000_L004_R1_001.fastq.gz"
    ).as_posix()
    with gzip.open(fastq_filename, "wb") as wh:
        wh.write(b"@A00689:73:XXXXXXXXX:4:1101:4806:1047 1:N:0:TCCTGGAACA+ACAACCAGTA")
    return fastq_filename


@pytest.fixture
def fastq_file_l_1_r_2(balsamic_housekeeper_dir):
    fastq_filename = Path(
        balsamic_housekeeper_dir, "XXXXXXXXX_000000_S000_L001_R2_001.fastq.gz"
    ).as_posix()
    with gzip.open(fastq_filename, "wb") as wh:
        wh.write(b"@A00689:73:XXXXXXXXX:1:1101:4806:1047 2:N:0:TCCTGGAACA+ACAACCAGTA")
    return fastq_filename


@pytest.fixture
def fastq_file_l_2_r_2(balsamic_housekeeper_dir):
    fastq_filename = Path(
        balsamic_housekeeper_dir, "XXXXXXXXX_000000_S000_L002_R2_001.fastq.gz"
    ).as_posix()
    with gzip.open(fastq_filename, "wb") as wh:
        wh.write(b"@A00689:73:XXXXXXXXX:2:1101:4806:1047 2:N:0:TCCTGGAACA+ACAACCAGTA")
    return fastq_filename


@pytest.fixture
def fastq_file_l_3_r_2(balsamic_housekeeper_dir):
    fastq_filename = Path(
        balsamic_housekeeper_dir, "XXXXXXXXX_000000_S000_L003_R2_001.fastq.gz"
    ).as_posix()
    with gzip.open(fastq_filename, "wb") as wh:
        wh.write(b"@A00689:73:XXXXXXXXX:3:1101:4806:1047 2:N:0:TCCTGGAACA+ACAACCAGTA")
    return fastq_filename


@pytest.fixture
def fastq_file_l_4_r_2(balsamic_housekeeper_dir):
    fastq_filename = Path(
        balsamic_housekeeper_dir, "XXXXXXXXX_000000_S000_L004_R2_001.fastq.gz"
    ).as_posix()
    with gzip.open(fastq_filename, "wb") as wh:
        wh.write(b"@A00689:73:XXXXXXXXX:4:1101:4806:1047 2:N:0:TCCTGGAACA+ACAACCAGTA")
    return fastq_filename


@pytest.fixture
def balsamic_mock_fastq_files(
    fastq_file_l_1_r_1,
    fastq_file_l_1_r_2,
    fastq_file_l_2_r_1,
    fastq_file_l_2_r_2,
    fastq_file_l_3_r_1,
    fastq_file_l_3_r_2,
    fastq_file_l_4_r_1,
    fastq_file_l_4_r_2,
):
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
def balsamic_housekeeper(housekeeper_api, helpers, balsamic_mock_fastq_files):

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
    balsamic_dir, balsamic_housekeeper_dir, balsamic_singularity_path, balsamic_reference_path,
) -> dict:
    # Dummy server config
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
        "housekeeper": {"database": "database", "root": balsamic_housekeeper_dir,},
        "lims": {"host": "example.db", "username": "testuser", "password": "testpassword",},
    }


@pytest.fixture(name="balsamic_lims")
def fixture_balsamic_lims():
    balsamic_lims = MockLimsAPI(server_config)

    balsamic_lims.add_capture_kit(
        internal_id="sample_case_wgs_paired_tumor", capture_kit=None,
    )
    balsamic_lims.add_capture_kit(
        internal_id="sample_case_wgs_paired_normal", capture_kit=None,
    )
    balsamic_lims.add_capture_kit(
        internal_id="sample_case_tgs_paired_tumor", capture_kit="BalsamicBed1",
    )
    balsamic_lims.add_capture_kit(
        internal_id="sample_case_tgs_paired_normal", capture_kit="BalsamicBed1",
    )
    balsamic_lims.add_capture_kit(
        internal_id="sample_case_wgs_single_tumor", capture_kit=None,
    )
    balsamic_lims.add_capture_kit(
        internal_id="sample_case_tgs_single_tumor", capture_kit="BalsamicBed1",
    )
    balsamic_lims.add_capture_kit(
        internal_id="sample_case_tgs_single_normal_error", capture_kit="BalsamicBed1",
    )
    balsamic_lims.add_capture_kit(
        internal_id="sample_case_tgs_paired_tumor_error", capture_kit="BalsamicBed1",
    )
    balsamic_lims.add_capture_kit(
        internal_id="sample_case_tgs_paired_tumor2_error", capture_kit="BalsamicBed1",
    )
    balsamic_lims.add_capture_kit(
        internal_id="sample_case_tgs_paired_normal_error", capture_kit="BalsamicBed1",
    )
    balsamic_lims.add_capture_kit(
        internal_id="mixed_sample_case_wgs_paired_tumor_error", capture_kit=None,
    )
    balsamic_lims.add_capture_kit(
        internal_id="mixed_sample_case_tgs_paired_normal_error", capture_kit="BalsamicBed1",
    )
    balsamic_lims.add_capture_kit(
        internal_id="mixed_sample_case_mixed_bed_paired_tumor_error", capture_kit="BalsamicBed1",
    )
    balsamic_lims.add_capture_kit(
        internal_id="mixed_sample_case_mixed_bed_paired_normal_error", capture_kit="BalsamicBed2",
    )
    balsamic_lims.add_capture_kit(
        internal_id="mip_sample_case_wgs_single_tumor", capture_kit=None,
    )

    return balsamic_lims


@pytest.fixture(name="balsamic_store")
def fixture_balsamic_store(base_store, helpers):
    """real store to be used in tests"""
    _store = base_store

    # Create tgs application version
    helpers.ensure_application_version(store=_store, application_tag="TGSA", application_type="tgs")

    # Create textbook case for WGS PAIRED
    case_wgs_paired = helpers.add_family(
        store=_store, internal_id="balsamic_case_wgs_paired", family_id="balsamic_case_wgs_paired"
    )
    sample_case_wgs_paired_tumor = helpers.add_sample(
        _store,
        internal_id="sample_case_wgs_paired_tumor",
        is_tumour=True,
        application_type="wgs",
        data_analysis="balsamic",
    )
    sample_case_wgs_paired_normal = helpers.add_sample(
        _store,
        internal_id="sample_case_wgs_paired_normal",
        is_tumour=False,
        application_type="wgs",
        data_analysis="balsamic",
    )
    helpers.add_relationship(_store, family=case_wgs_paired, sample=sample_case_wgs_paired_tumor)
    helpers.add_relationship(_store, family=case_wgs_paired, sample=sample_case_wgs_paired_normal)

    # Create textbook case for TGS PAIRED
    case_tgs_paired = helpers.add_family(
        _store, internal_id="balsamic_case_tgs_paired", family_id="balsamic_case_tgs_paired"
    )
    sample_case_tgs_paired_tumor = helpers.add_sample(
        _store,
        internal_id="sample_case_tgs_paired_tumor",
        is_tumour=True,
        application_tag="TGSA",
        application_type="tgs",
        data_analysis="BALSAMIC",
    )
    sample_case_tgs_paired_normal = helpers.add_sample(
        _store,
        internal_id="sample_case_tgs_paired_normal",
        is_tumour=False,
        application_tag="TGSA",
        application_type="tgs",
        data_analysis="MIP+BALSAMIC",
    )
    helpers.add_relationship(_store, family=case_tgs_paired, sample=sample_case_tgs_paired_tumor)
    helpers.add_relationship(_store, family=case_tgs_paired, sample=sample_case_tgs_paired_normal)

    # Create textbook case for WGS TUMOR ONLY
    case_wgs_single = helpers.add_family(
        _store, internal_id="balsamic_case_wgs_single", family_id="balsamic_case_wgs_single"
    )
    sample_case_wgs_single_tumor = helpers.add_sample(
        _store,
        internal_id="sample_case_wgs_single_tumor",
        is_tumour=True,
        application_type="wgs",
        data_analysis="balsamic",
    )
    helpers.add_relationship(_store, family=case_wgs_single, sample=sample_case_wgs_single_tumor)

    # Create textbook case for TGS TUMOR ONLY
    case_tgs_single = helpers.add_family(
        _store, internal_id="balsamic_case_tgs_single", family_id="balsamic_case_tgs_single"
    )
    sample_case_tgs_single_tumor = helpers.add_sample(
        _store,
        internal_id="sample_case_tgs_single_tumor",
        is_tumour=True,
        application_tag="TGSA",
        application_type="tgs",
        data_analysis="balsamic",
    )
    helpers.add_relationship(_store, family=case_tgs_single, sample=sample_case_tgs_single_tumor)

    # Create ERROR case for TGS NORMAL ONLY
    case_tgs_single_error = helpers.add_family(
        _store,
        internal_id="balsamic_case_tgs_single_error",
        family_id="balsamic_case_tgs_single_error",
    )
    sample_case_tgs_single_normal_error = helpers.add_sample(
        _store,
        internal_id="sample_case_tgs_single_normal_error",
        is_tumour=False,
        application_tag="TGSA",
        application_type="tgs",
        data_analysis="balsamic",
    )
    helpers.add_relationship(
        _store, family=case_tgs_single_error, sample=sample_case_tgs_single_normal_error
    )

    # Create ERROR case for TGS TWO TUMOR ONE NORMAL
    case_tgs_paired_error = helpers.add_family(
        _store,
        internal_id="balsamic_case_tgs_paired_error",
        family_id="balsamic_case_tgs_paired_error",
    )
    sample_case_tgs_paired_tumor_error = helpers.add_sample(
        _store,
        internal_id="sample_case_tgs_paired_tumor_error",
        is_tumour=True,
        application_tag="TGSA",
        application_type="tgs",
        data_analysis="balsamic",
    )
    sample_case_tgs_paired_tumor2_error = helpers.add_sample(
        _store,
        internal_id="sample_case_tgs_paired_tumor2_error",
        is_tumour=True,
        application_tag="TGSA",
        application_type="tgs",
        data_analysis="balsamic",
    )
    sample_case_tgs_paired_normal_error = helpers.add_sample(
        _store,
        internal_id="sample_case_tgs_paired_normal_error",
        is_tumour=False,
        application_tag="TGSA",
        application_type="tgs",
        data_analysis="balsamic",
    )
    helpers.add_relationship(
        _store, family=case_tgs_paired_error, sample=sample_case_tgs_paired_tumor_error
    )
    helpers.add_relationship(
        _store, family=case_tgs_paired_error, sample=sample_case_tgs_paired_tumor2_error
    )
    helpers.add_relationship(
        _store, family=case_tgs_paired_error, sample=sample_case_tgs_paired_normal_error
    )

    # Create ERROR case for MIXED application type
    case_mixed_paired_error = helpers.add_family(
        _store,
        internal_id="balsamic_case_mixed_paired_error",
        family_id="balsamic_case_mixed_paired_error",
    )
    mixed_sample_case_wgs_paired_tumor_error = helpers.add_sample(
        _store,
        internal_id="mixed_sample_case_wgs_paired_tumor_error",
        is_tumour=True,
        application_type="wgs",
        data_analysis="balsamic",
    )
    mixed_sample_case_tgs_paired_normal_error = helpers.add_sample(
        _store,
        internal_id="mixed_sample_case_tgs_paired_normal_error",
        is_tumour=False,
        application_tag="TGSA",
        application_type="tgs",
        data_analysis="balsamic",
    )
    helpers.add_relationship(
        _store, family=case_mixed_paired_error, sample=mixed_sample_case_wgs_paired_tumor_error
    )
    helpers.add_relationship(
        _store, family=case_mixed_paired_error, sample=mixed_sample_case_tgs_paired_normal_error
    )

    # Create ERROR case for MIXED application type NOT BALSAMIC APPLICATION
    case_mixed_wgs_mic_paired_error = helpers.add_family(
        _store,
        internal_id="balsamic_case_mixed_wgs_mic_paired_error",
        family_id="balsamic_case_mixed_wgs_mic_paired_error",
    )
    mixed_sample_case_wgs_mic_paired_tumor_error = helpers.add_sample(
        _store,
        internal_id="mixed_sample_case_wgs_mic_paired_tumor_error",
        is_tumour=True,
        application_type="wgs",
        data_analysis="balsamic",
    )
    mixed_sample_case_wgs_mic_paired_normal_error = helpers.add_sample(
        _store,
        internal_id="mixed_sample_case_wgs_mic_paired_normal_error",
        is_tumour=False,
        application_tag="MICA",
        application_type="mic",
        data_analysis="balsamic",
    )
    helpers.add_relationship(
        _store,
        family=case_mixed_wgs_mic_paired_error,
        sample=mixed_sample_case_wgs_mic_paired_tumor_error,
    )
    helpers.add_relationship(
        _store,
        family=case_mixed_wgs_mic_paired_error,
        sample=mixed_sample_case_wgs_mic_paired_normal_error,
    )

    # Create ERROR case for MIXED TARGET BED
    case_mixed_bed_paired_error = helpers.add_family(
        _store,
        internal_id="balsamic_case_mixed_bed_paired_error",
        family_id="balsamic_case_mixed_bed_paired_error",
    )
    mixed_sample_case_mixed_bed_paired_tumor_error = helpers.add_sample(
        _store,
        internal_id="mixed_sample_case_mixed_bed_paired_tumor_error",
        is_tumour=True,
        application_tag="TGSA",
        application_type="tgs",
        data_analysis="balsamic",
    )
    mixed_sample_case_mixed_bed_paired_normal_error = helpers.add_sample(
        _store,
        internal_id="mixed_sample_case_mixed_bed_paired_normal_error",
        is_tumour=False,
        application_tag="TGSA",
        application_type="tgs",
        data_analysis="balsamic",
    )
    helpers.add_relationship(
        _store,
        family=case_mixed_bed_paired_error,
        sample=mixed_sample_case_mixed_bed_paired_tumor_error,
    )
    helpers.add_relationship(
        _store,
        family=case_mixed_bed_paired_error,
        sample=mixed_sample_case_mixed_bed_paired_normal_error,
    )

    # Create ERROR case for WGS TUMOR ONLY MIP ANALYSIS ONLY
    mip_case_wgs_single = helpers.add_family(
        _store, internal_id="mip_case_wgs_single", family_id="mip_case_wgs_single"
    )
    mip_sample_case_wgs_single_tumor = helpers.add_sample(
        _store,
        internal_id="mip_sample_case_wgs_single_tumor",
        is_tumour=True,
        application_type="wgs",
        data_analysis="mip",
    )
    helpers.add_relationship(
        _store, family=mip_case_wgs_single, sample=mip_sample_case_wgs_single_tumor
    )

    # Create ERROR case with NO SAMPLES
    helpers.add_family(
        _store, internal_id="no_sample_case", family_id="no_sample_case"
    )


    # Create BED1 version 1
    bed1_name = "BalsamicBed1"
    bed1_filename = "balsamic_bed_1.bed"
    bed1 = _store.add_bed(name=bed1_name)
    _store.add_commit(bed1)
    version1 = _store.add_bed_version(
        bed=bed1, version=1, filename=bed1_filename, shortname=bed1_name
    )
    _store.add_commit(version1)

    # Create BED2 version 1
    bed2_name = "BalsamicBed2"
    bed2_filename = "balsamic_bed_2.bed"
    bed2 = _store.add_bed(name=bed2_name)
    _store.add_commit(bed2)
    version2 = _store.add_bed_version(
        bed=bed2, version=1, filename=bed2_filename, shortname=bed2_name
    )
    _store.add_commit(version2)

    return _store


@pytest.fixture
def balsamic_context(server_config, balsamic_store, balsamic_lims, balsamic_housekeeper) -> dict:
    """context to use in cli"""
    balsamic_analysis_api = BalsamicAnalysisAPI(
        balsamic_api=BalsamicAPI(server_config),
        store=balsamic_store,
        housekeeper_api=balsamic_housekeeper,
        fastq_handler=FastqHandler,
        lims_api=balsamic_lims,
        fastq_api=FastqAPI,
    )
    return {
        "BalsamicAnalysisAPI": balsamic_analysis_api,
    }
