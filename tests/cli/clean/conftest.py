"""Fixtures for cli clean tests"""

import datetime as dt
from pathlib import Path

import pytest

from cg.apps.balsamic.api import BalsamicAPI
from cg.apps.hk import HousekeeperAPI
from cg.meta.workflow.balsamic import BalsamicAnalysisAPI
from cg.store import Store


@pytest.fixture
def balsamic_clean_store(base_store: Store, timestamp_yesterday: dt.datetime, helpers) -> Store:
    store = base_store

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
        family=case_to_clean,
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
def server_config(balsamic_dir: Path) -> dict:
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
            "root": balsamic_dir,
        },
        "lims": {
            "host": "example.db",
            "username": "testuser",
            "password": "testpassword",
        },
    }


@pytest.fixture
def balsamic_analysis_api(
    server_config: dict,
    balsamic_clean_store: Store,
    housekeeper_api: HousekeeperAPI,
    trailblazer_api,
):
    return BalsamicAnalysisAPI(
        balsamic_api=BalsamicAPI(server_config),
        store=balsamic_clean_store,
        housekeeper_api=housekeeper_api,
        fastq_handler="FastqHandler",
        lims_api="LIMS",
        trailblazer_api=trailblazer_api,
    )


@pytest.fixture
def clean_context(
    base_store: Store,
    housekeeper_api: HousekeeperAPI,
    balsamic_analysis_api: BalsamicAnalysisAPI,
    helpers,
    tmpdir,
) -> dict:
    """context to use in cli"""

    return {
        "housekeeper_api": housekeeper_api,
        "store_api": balsamic_clean_store,
        "BalsamicAnalysisAPI": balsamic_analysis_api,
    }
