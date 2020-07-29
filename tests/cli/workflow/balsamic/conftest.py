"""Fixtures for cli balsamic tests"""

from pathlib import Path

import pytest

from cg.apps.balsamic.fastq import FastqHandler
from cg.apps.lims import LimsAPI
from cg.meta.workflow.balsamic import BalsamicAnalysisAPI
from cg.store import Store, models
from cg.utils.fastq import FastqAPI
from cg.apps.balsamic.api import BalsamicAPI


class MockLimsAPI:
    """WIP"""

    def __init__(self):
        pass


class MockHousekeeperAPI:
    """WIP"""

    def __init__(self):
        pass


@pytest.fixture(name="balsamic_dir")
def fixture_balsamic_dir(tmpdir_factory, apps_dir: Path) -> Path:
    """Return the path to the balsamic apps dir"""
    balsamic_dir = tmpdir_factory.mktemp(Path(apps_dir, "balsamic"), numbered=False)
    return balsamic_dir


@pytest.fixture(name="balsamic_housekeeper_dir")
def fixture_balsamic_housekeeeper_dir(tmpdir_factory, apps_dir: Path) -> Path:
    """Return the path to the balsamic housekeeper dir"""
    balsamic_housekeeper_dir = tmpdir_factory.mktemp(
        Path(apps_dir, "balsamic", "bundles"), numbered=False
    )
    return balsamic_housekeeper_dir


@pytest.fixture(name="balsamic_singularity_path")
def fixture_balsamic_singularity_path(balsamic_dir) -> Path:
    balsamic_singularity_path = Path(balsamic_dir, "singularity.sif")
    balsamic_singularity_path.touch(exist_ok=True)
    return balsamic_singularity_path.as_posix()


@pytest.fixture(name="balsamic_bed_path")
def fixture_balsamic_bed_path(balsamic_dir) -> Path:
    balsamic_bed_path = Path(balsamic_dir, "Bed.bed")
    balsamic_bed_path.touch(exist_ok=True)
    return balsamic_bed_path.as_posix()


@pytest.fixture(name="balsamic_reference_path")
def fixture_balsamic_reference_path(balsamic_dir) -> Path:
    balsamic_reference_path = Path(balsamic_dir, "reference.json")
    balsamic_reference_path.touch(exist_ok=True)
    return balsamic_reference_path.as_posix()


@pytest.fixture
def server_config(
    tmpdir_factory,
    balsamic_dir,
    balsamic_housekeeper_dir,
    balsamic_bed_path,
    balsamic_singularity_path,
    balsamic_reference_path,
) -> dict:
    # Dummy server config
    return {
        "database": "test_db",
        "bed_path": balsamic_bed_path,
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
        "housekeeper": {"database": "test_db_housekeeper", "root": balsamic_housekeeper_dir,},
        "lims": {"host": "example.db", "username": "testuser", "password": "testpassword",},
    }


@pytest.fixture
def balsamic_context(server_config, balsamic_store) -> dict:
    """context to use in cli"""
    balsamic_analysis_api = BalsamicAnalysisAPI(config=server_config)
    balsamic_analysis_api.store = balsamic_store
    balsamic_analysis_api.lims_api = MockLimsAPI()
    balsamic_analysis_api.housekeeper_api = MockHousekeeperAPI()
    return {
        "BalsamicAnalysisAPI": balsamic_analysis_api,
    }


@pytest.fixture(scope="function", name="balsamic_store")
def fixture_balsamic_store(base_store: Store, lims_api, helpers) -> Store:
    """real store to be used in tests"""
    _store = base_store

    # Create textbook case for WGS PAIRED
    case_wgs_paired = helpers.add_family(_store, "balsamic_case_wgs_paired")
    sample_case_wgs_paired_tumor = helpers.add_sample(
        _store,
        "sample_case_wgs_paired_tumor",
        is_tumour=True,
        application_type="wgs",
        data_analysis="balsamic",
    )
    sample_case_wgs_paired_normal = helpers.add_sample(
        _store,
        "sample_case_wgs_paired_normal",
        is_tumour=False,
        application_type="wgs",
        data_analysis="balsamic",
    )
    helpers.add_relationship(_store, family=case_wgs_paired, sample=sample_case_wgs_paired_tumor)
    helpers.add_relationship(_store, family=case_wgs_paired, sample=sample_case_wgs_paired_normal)

    # Create textbook case for TGS PAIRED
    case_tgs_paired = helpers.add_family(_store, "balsamic_case_tgs_paired")
    sample_case_tgs_paired_tumor = helpers.add_sample(
        _store,
        "sample_case_tgs_paired_tumor",
        is_tumour=True,
        application_type="tgs",
        data_analysis="balsamic",
    )
    sample_case_tgs_paired_normal = helpers.add_sample(
        _store,
        "sample_case_tgs_paired_normal",
        is_tumour=False,
        application_type="tgs",
        data_analysis="balsamic",
    )
    helpers.add_relationship(_store, family=case_tgs_paired, sample=sample_case_tgs_paired_tumor)
    helpers.add_relationship(_store, family=case_tgs_paired, sample=sample_case_tgs_paired_normal)

    # Create textbook case for WGS TUMOR ONLY
    case_wgs_single = helpers.add_family(_store, "balsamic_case_wgs_single")
    sample_case_wgs_single_tumor = helpers.add_sample(
        _store,
        "sample_case_wgs_single_tumor",
        is_tumour=True,
        application_type="wgs",
        data_analysis="balsamic",
    )
    helpers.add_relationship(_store, family=case_wgs_single, sample=sample_case_wgs_single_tumor)

    # Create textbook case for TGS TUMOR ONLY
    case_tgs_single = helpers.add_family(_store, "balsamic_case_tgs_single")
    sample_case_tgs_single_tumor = helpers.add_sample(
        _store,
        "sample_case_tgs_single_tumor",
        is_tumour=True,
        application_type="tgs",
        data_analysis="balsamic",
    )
    helpers.add_relationship(_store, family=case_tgs_single, sample=sample_case_tgs_single_tumor)

    # Create ERROR case for TGS NORMAL ONLY
    case_tgs_single_error = helpers.add_family(_store, "balsamic_case_tgs_single_error")
    sample_case_tgs_single_normal_error = helpers.add_sample(
        _store,
        "sample_case_tgs_single_normal_error",
        is_tumour=False,
        application_type="tgs",
        data_analysis="balsamic",
    )
    helpers.add_relationship(
        _store, family=case_tgs_single_error, sample=sample_case_tgs_single_normal_error
    )

    # Create ERROR case for TGS TWO TUMOR ONE NORMAL
    case_tgs_paired_error = helpers.add_family(_store, "balsamic_case_tgs_paired_error")
    sample_case_tgs_paired_tumor_error = helpers.add_sample(
        _store,
        "sample_case_tgs_paired_tumor_error",
        is_tumour=True,
        application_type="tgs",
        data_analysis="balsamic",
    )
    sample_case_tgs_paired_tumor2_error = helpers.add_sample(
        _store,
        "sample_case_tgs_paired_tumor2_error",
        is_tumour=True,
        application_type="tgs",
        data_analysis="balsamic",
    )
    sample_case_tgs_paired_normal_error = helpers.add_sample(
        _store,
        "sample_case_tgs_paired_normal_error",
        is_tumour=False,
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
    case_mixed_paired_error = helpers.add_family(_store, "balsamic_case_mixed_paired_error")
    mixed_sample_case_wgs_paired_tumor_error = helpers.add_sample(
        _store,
        "mixed_sample_case_wgs_paired_tumor_error",
        is_tumour=True,
        application_type="wgs",
        data_analysis="balsamic",
    )
    mixed_sample_case_tgs_paired_normal_error = helpers.add_sample(
        _store,
        "mixed_sample_case_tgs_paired_normal_error",
        is_tumour=False,
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
        _store, "balsamic_case_mixed_wgs_mic_paired_error"
    )
    mixed_sample_case_wgs_mic_paired_tumor_error = helpers.add_sample(
        _store,
        "mixed_sample_case_wgs_mic_paired_tumor_error",
        is_tumour=True,
        application_type="wgs",
        data_analysis="balsamic",
    )
    mixed_sample_case_wgs_mic_paired_normal_error = helpers.add_sample(
        _store,
        "mixed_sample_case_wgs_mic_paired_normal_error",
        is_tumour=False,
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
    case_mixed_bed_paired_error = helpers.add_family(_store, "balsamic_case_mixed_bed_paired_error")
    mixed_sample_case_mixed_bed_paired_tumor_error = helpers.add_sample(
        _store,
        "mixed_sample_case_mixed_bed_paired_tumor_error",
        is_tumour=True,
        application_type="tgs",
        data_analysis="balsamic",
    )
    mixed_sample_case_mixed_bed_paired_normal_error = helpers.add_sample(
        _store,
        "mixed_sample_case_mixed_bed_paired_normal_error",
        is_tumour=False,
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
    mip_case_wgs_single = helpers.add_family(_store, "mip_case_wgs_single")
    mip_sample_case_wgs_single_tumor = helpers.add_sample(
        _store,
        "mip_sample_case_wgs_single_tumor",
        is_tumour=True,
        application_type="wgs",
        data_analysis="mip",
    )
    helpers.add_relationship(
        _store, family=mip_case_wgs_single, sample=mip_sample_case_wgs_single_tumor
    )

    return _store
