import pytest
import datetime as dt

from pathlib import Path
from ruamel.yaml import YAML

from cg.apps.tb import TrailblazerAPI
from cg.meta.workflow.mip import AnalysisAPI
from cg.store.models import Family
from cg.store import Store
from cg.apps.hk import HousekeeperAPI
from tests.mocks.limsmock import MockLimsAPI

from trailblazer.store.models import Analysis as tb_Analysis


@pytest.fixture
def mip_lims():
    mip_lims = MockLimsAPI({})
    return mip_lims


@pytest.fixture
def mock_root_folder():
    return "/var/empty"


@pytest.fixture(name="mip_test_dir")
def mip_test_dir(project_dir: Path) -> Path:
    """Return the path to the mip apps dir"""
    mip_test = project_dir / "mip_test"
    mip_test.mkdir(parents=True, exist_ok=True)
    return mip_test


@pytest.fixture(name="mip_case_ids")
def mip_case_ids() -> dict:
    """Create a list of case ids"""

    case_ids = {
        "yellowhog": {"textbook": True, "name": "F0000001"},
        "purplesnail": {"textbook": False, "name": "F0000003"},
        "bluezebra": {"textbook": True, "name": "F0000002"},
    }

    return case_ids


@pytest.fixture(name="mip_configs")
def make_mip_configs(mip_case_ids: dict, mip_test_dir: Path) -> dict:
    """Create a dictionary of textbook and corrupt configs for mip."""

    yaml = YAML()

    # Storing paths in a list to be returned and used in later stages.

    config_dict = {}

    for case in mip_case_ids:
        if mip_case_ids[case]["textbook"]:
            config = {
                "email": "fake_email@notscilifelab.com",
                "case_id": case,
                "samples": "dummy_samples",
                "is_dryrun": False,
                "outdata_dir": str(mip_test_dir),
                "priority": "medium",
                "sample_info_file": str(Path(mip_test_dir / case / f"{case}_qc_sample_info.yaml")),
                "analysis_type": {"ACC00000": "wgs"},
                "slurm_quality_of_service": "medium",
            }
            case_dir = mip_test_dir / case
            case_dir.mkdir(parents=True, exist_ok=True)
            config_path = case_dir / f"{case}_config.yaml"
            config_dict[case] = config_path
            with open(config_path, "wb") as fh:
                yaml.dump(config, fh)

        elif not mip_case_ids[case]["textbook"]:
            config = {
                "email": "fake_email@notscilifelab.com",
                "case_id": case,
                "samples": "dummy_samples",
                "is_dryrun": False,
                "outdata_dir": str(mip_test_dir),
                "priority": "medium",
                "sample_info_file": "/path/in/to/the/void",
                "analysis_type": {"ACC00000": "wgs"},
                "slurm_quality_of_service": "medium",
            }

            case_dir = mip_test_dir / case
            case_dir.mkdir(parents=True, exist_ok=True)
            config_path = case_dir / f"{case}_config.yaml"
            config_dict[case] = config_path
            with open(config_path, "w") as fh:
                yaml.dump(config, fh)

    return config_dict


@pytest.fixture(name="mip_qc_sample_info")
def make_mip_sample_infos(mip_case_ids: dict, mip_test_dir: Path) -> dict:
    """Create qc sample info files for cases"""

    yaml = YAML()

    # Store paths in a list to be used in other stages

    qc_sample_info_list = {}

    for case in mip_case_ids:
        sample_info_data = {
            "date": dt.datetime.now(),
            "analysisrunstatus": "finished",
            "analysis_date": dt.datetime.now(),
            "case": case,
            "mip_version": "latest",
        }

        case_dir = mip_test_dir / case
        case_dir.mkdir(parents=True, exist_ok=True)
        sample_info_path = case_dir / f"{case}_qc_sample_info.yaml"
        qc_sample_info_list[case] = sample_info_path
        with open(sample_info_path, "w") as fh:
            yaml.dump(sample_info_data, fh)

    return qc_sample_info_list


@pytest.fixture(name="mip_deliverables")
def make_mip_deliverables(mip_case_ids: dict, mip_test_dir: Path) -> dict:
    """Create deliverables for mip store testing"""

    yaml = YAML()

    # Create a dict of paths to the deliverables to be used in later stages

    mip_deliverables = {}

    return mip_deliverables


@pytest.fixture(name="_store")
def populated_store(base_store: Store, mip_case_ids: dict, helpers) -> Store:
    """Create and populate temporary db with test cases for mip"""

    _store = base_store

    # Add textbook families to db

    for case in mip_case_ids:
        helpers.add_family(
            store=_store,
            internal_id=case,
            family_id=mip_case_ids[case]["name"],
            customer_id="cust000"
        )

    return _store


@pytest.fixture(name="_housekeeper_api")
def populate_mip_housekeeper(
        real_housekeeper_api: HousekeeperAPI,
        mip_case_ids: dict,
        mip_qc_sample_info: dict,
        mip_configs: dict,
        helpers) -> HousekeeperAPI:
    """Create and populate temporary hk with good and bad test cases for mip"""

    _housekeeper_api = real_housekeeper_api

    for case in mip_case_ids:
        bundle_data = {
            "name": case,
            "created": dt.datetime.now(),
            "started_at": dt.datetime.now(),
            "files": [
                {
                    "path": str(mip_qc_sample_info[case]),
                    "tags": ["qcmetrics"], "archive": False
                },
                {
                    "path": str(mip_configs[case]),
                    "tags": ["mip-config"], "archive": False
                }
            ]
        }
        helpers.ensure_hk_bundle(store=_housekeeper_api, bundle_data=bundle_data)

    return _housekeeper_api


@pytest.fixture(name="_tb_api")
def populated_tb(
        trailblazer_api: TrailblazerAPI,
        mip_case_ids: dict,
        mip_configs: dict,
        mip_test_dir: Path) -> TrailblazerAPI:
    """Create and populate a trailblazer api with cases"""

    _tb_api = trailblazer_api

    for case in mip_case_ids:
        _tb_api.add_commit(
            tb_Analysis(
                family=case,
                status="completed",
                deleted=False,
                config_path=str(mip_configs[case])
            )
        )

    return _tb_api


@pytest.fixture
def mip_context(analysis_store_single_case, tb_api, housekeeper_api, mip_lims, mock_root_folder):
    return {
        "dna_api": AnalysisAPI(
            db=analysis_store_single_case,
            hk_api=housekeeper_api,
            tb_api=tb_api,
            scout_api="scout_api",
            lims_api=mip_lims,
            deliver_api="deliver",
            script="echo",
            pipeline="analyse rd_dna",
            conda_env="S_mip_rd-dna",
            root=mock_root_folder,
        ),
        "rna_api": AnalysisAPI(
            db=analysis_store_single_case,
            hk_api=housekeeper_api,
            tb_api=tb_api,
            scout_api="scout_api",
            lims_api=mip_lims,
            deliver_api="deliver",
            script="echo",
            pipeline="analyse rd_rna",
            conda_env="S_mip_rd-rna",
            root=mock_root_folder,
        ),
        "mip-rd-dna": {
            "conda_env": "S_mip_rd-dna",
            "mip_config": "config.yaml",
            "pipeline": "analyse rd_dna",
            "root": mock_root_folder,
            "script": "echo",
        },
        "mip-rd-rna": {
            "conda_env": "S_mip_rd-rna",
            "mip_config": "config.yaml",
            "pipeline": "analyse rd_rna",
            "root": mock_root_folder,
            "script": "echo",
        },
    }


@pytest.fixture(name="mip_store_context")
def mip_store_context(_tb_api: TrailblazerAPI, _store: Store, _housekeeper_api: HousekeeperAPI) -> dict:
    """Create a context to be used in testing mip store, this should be fused with mip_context above at later stages"""
    return {"tb_api": _tb_api, "hk_api": _housekeeper_api, "db": _store}