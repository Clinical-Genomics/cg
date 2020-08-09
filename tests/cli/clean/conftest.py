"""Fixtures for cli clean tests"""
from pathlib import Path
import pytest
import datetime as dt

from cg.meta.workflow.balsamic import BalsamicAnalysisAPI
from cg.apps.balsamic.api import BalsamicAPI


@pytest.fixture
def balsamic_clean_store(base_store, helpers):
    store = base_store
    timestamp_yesterday = dt.datetime.now() - dt.timedelta(days=1)

    # Create textbook case for cleaning
    case_to_clean = helpers.add_family(
        store=store, internal_id="balsamic_case_clean", family_id="balsamic_case_clean"
    )
    sample_case_to_clean = helpers.add_sample(
        store,
        internal_id="balsamic_sample_clean",
        is_tumour=True,
        application_type="wgs",
        data_analysis="balsamic",
    )
    helpers.add_relationship(store, family=case_to_clean, sample=sample_case_to_clean)

    helpers.add_analysis(
        store,
        family = case_to_clean,
        pipeline="balsamic",
        started_at=timestamp_yesterday,
        uploaded_at=timestamp_yesterday,
        cleaned_at=None,
    )
    return store



@pytest.fixture(name="balsamic_dir")
def balsamic_dir(tmpdir_factory, apps_dir: Path) -> Path:
    """Return the path to the balsamic apps dir"""
    balsamic_dir = tmpdir_factory.mktemp("balsamic")
    return Path(balsamic_dir).absolute().as_posix()

@pytest.fixture
def server_config(balsamic_dir):
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
        "housekeeper": {"database": "database", "root": balsamic_dir,},
        "lims": {"host": "example.db", "username": "testuser", "password": "testpassword",},
    }

@pytest.fixture
def balsamic_analysis_api(server_config, balsamic_clean_store, housekeeper_api):
    return BalsamicAnalysisAPI(
        balsamic_api=BalsamicAPI(server_config),
        store=balsamic_clean_store,
        housekeeper_api=housekeeper_api,
        fastq_handler="FastqHandler",
        lims_api="LIMS",
        fastq_api="FastqAPI",
    )


@pytest.fixture
def clean_context(base_store, housekeeper_api, balsamic_analysis_api, helpers, tmpdir) -> dict:
    """context to use in cli"""

    return {"hk_api": housekeeper_api, "store_api": balsamic_clean_store, "BalsamicAnalysisAPI": balsamic_analysis_api}


