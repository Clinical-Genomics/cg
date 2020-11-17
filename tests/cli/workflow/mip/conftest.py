from typing import Any, Union

import pytest
import copy
import datetime as dt

from cg.constants import Pipeline
from cg.meta.workflow.mip import MipAnalysisAPI
from pathlib import Path
from ruamel.yaml import YAML

from cg.apps.tb import TrailblazerAPI
from cg.apps.tb.models import TrailblazerAnalysis
from cg.meta.workflow.mip import MipAnalysisAPI
from cg.store import Store
from cg.apps.hk import HousekeeperAPI
from tests.mocks.limsmock import MockLimsAPI
from tests.mocks.tb_mock import MockTB

from trailblazer.store.models import Analysis as tb_Analysis


@pytest.fixture
def mip_lims():
    mip_lims = MockLimsAPI({})
    return mip_lims


@pytest.fixture
def mock_root_folder(project_dir):
    return Path(project_dir, "cases").as_posix()


@pytest.fixture(name="mip_case_ids")
def fixture_mip_case_ids() -> dict:
    """Dictionary of case ids, connected samples, their name and if they should fail (textbook or not)"""

    case_ids = {
        "yellowhog": {
            "textbook": True,
            "name": "F0000001",
            "internal_id": "ACC00000",
        },
        "purplesnail": {
            "textbook": False,
            "name": "F0000003",
            "internal_id": "ACC00000",
        },
        "bluezebra": {
            "textbook": True,
            "name": "F0000002",
            "internal_id": "ACC00000",
        },
    }

    return case_ids


@pytest.fixture(name="mip_case_dirs")
def fixture_mip_case_dirs(mip_case_ids: dict, project_dir: Path) -> dict:
    """Create case directories and return a dictionary of the tmpdir paths"""

    mip_case_dirs = {}

    for case in mip_case_ids:
        case_dir = Path(project_dir / "cases" / case)
        case_dir.mkdir(exist_ok=True, parents=True)
        mip_case_dirs[case] = case_dir

    return mip_case_dirs


@pytest.fixture(name="mip_deliverables")
def fixture_mip_deliverables(
    mip_case_ids: dict,
    mip_case_dirs: dict,
    mip_deliverables_file: Path,
) -> dict:
    """Create deliverables for mip store testing"""

    yaml = YAML()

    # Create a dict of paths to the deliverables to be used in later stages
    deliverables_paths = {}

    # Load general deliverables file
    with open(mip_deliverables_file, "r") as mip_dna_deliverables:
        mip_deliverables = yaml.load(mip_dna_deliverables)

    for case in mip_case_ids:
        if mip_case_ids[case]["textbook"]:
            case_specific_deliverables = copy.deepcopy(mip_deliverables)

            for file in case_specific_deliverables["files"]:
                if file["path_index"]:
                    file["path_index"] = str(mip_case_dirs[case] / Path(file["path_index"]).name)
                    # Touch the tmp file
                    open(file["path_index"], "a").close()
                file["path"] = str(mip_case_dirs[case] / Path(file["path"]).name)
                # Touch the tmp file
                open(file["path"], "a").close()

            case_deliverables_path = mip_case_dirs[case] / f"{case}_deliverables.yaml"
            with open(case_deliverables_path, "w") as fh:
                yaml.dump(case_specific_deliverables, fh)
            deliverables_paths[case] = case_deliverables_path

        elif not mip_case_ids[case]["textbook"]:
            case_deliverables_path = mip_case_dirs[case] / f"{case}_deliverables.yaml"
            with open(case_deliverables_path, "w") as fh:
                yaml.dump({"files": []}, fh)
            deliverables_paths[case] = case_deliverables_path

    return deliverables_paths


@pytest.fixture(name="mip_qc_sample_info")
def fixture_mip_qc_sample_info(mip_case_ids: dict, mip_case_dirs: dict) -> dict:
    """Create qc sample info files for cases"""

    yaml = YAML()

    # Store paths in a list to be used in other stages

    qc_sample_info = {}

    for case in mip_case_ids:
        sample_info_data = {
            "date": dt.datetime.now(),
            "analysisrunstatus": "finished",
            "analysis_date": dt.datetime.now(),
            "case": case,
            "mip_version": "latest",
        }

        sample_info_path = mip_case_dirs[case] / f"{case}_qc_sample_info.yaml"
        qc_sample_info[case] = sample_info_path
        with open(sample_info_path, "w") as fh:
            yaml.dump(sample_info_data, fh)

    return qc_sample_info


@pytest.fixture(name="mip_configs")
def fixture_mip_configs(
    mip_case_ids: dict, mip_case_dirs: dict, mip_deliverables: dict, mip_qc_sample_info: dict
) -> dict:
    """Create config files for mip case"""

    yaml = YAML()

    # Storing paths in a list to be returned and used in later stages.

    config_dict = {}

    for case in mip_case_ids:
        config = {
            "email": "fake_email@notscilifelab.com",
            "case_id": case,
            "samples": "dummy_samples",
            "is_dryrun": False,
            "outdata_dir": str(mip_case_dirs[case]),
            "priority": "medium",
            "sampleinfo_path": str(mip_qc_sample_info[case]),
            "sample_info_file": str(mip_qc_sample_info[case]),
            "analysis_type": {mip_case_ids[case]["internal_id"]: "wgs"},
            "slurm_quality_of_service": "medium",
            "store_file": str(mip_deliverables[case]),
        }
        analysis_path = Path(mip_case_dirs[case] / "analysis")
        Path(analysis_path).mkdir(parents=True, exist_ok=True)
        config_path = analysis_path / f"{case}_config.yaml"
        config_dict[case] = config_path
        with open(config_path, "w") as fh:
            yaml.dump(config, fh)

    return config_dict


@pytest.fixture(name="_store")
def fixture_store(base_store: Store, mip_case_ids: dict, helpers) -> Store:
    """Create and populate temporary db with test cases for mip"""

    _store = base_store

    # Add apptag to db

    helpers.ensure_application_version(store=_store, application_tag="WGSA", application_type="wgs")

    # Add sample, cases and relationships to db

    for case in mip_case_ids:
        family = helpers.add_family(
            store=_store,
            internal_id=case,
            family_id=mip_case_ids[case]["name"],
        )
        sample = helpers.add_sample(
            store=_store,
            sample=mip_case_ids[case]["internal_id"],
            data_analysis=Pipeline.MIP_DNA,
            customer_name="cust000",
            application_tag="WGSA",
            application_type="wgs",
            gender="unknown",
        )
        helpers.add_relationship(store=_store, sample=sample, family=family, status="affected")

    return _store


@pytest.fixture(name="empty_housekeeper_api")
def fixture_empty_housekeeper_api(real_housekeeper_api: HousekeeperAPI) -> HousekeeperAPI:
    """Empty housekeeper for testing store in mip workflow"""

    _housekeeper_api = real_housekeeper_api

    return _housekeeper_api


@pytest.fixture(name="populated_mip_tb_api")
def fixture_populated_mip_tb_api(
    trailblazer_api: TrailblazerAPI, mip_case_ids: dict, mip_configs: dict
) -> TrailblazerAPI:
    """Trailblazer api filled with mip cases"""

    _tb_api = trailblazer_api

    for case in mip_case_ids:
        _tb_api.add_commit(
            tb_Analysis(
                family=case, status="completed", deleted=False, config_path=str(mip_configs[case])
            )
        )

    return _tb_api


@pytest.fixture
def mip_context(
    analysis_store_single_case, trailblazer_api, housekeeper_api, mip_lims, mock_root_folder
):
    return {
        "dna_api": MipAnalysisAPI(
            db=analysis_store_single_case,
            hk_api=housekeeper_api,
            tb_api=trailblazer_api,
            scout_api="scout_api",
            lims_api=mip_lims,
            script="echo",
            pipeline="analyse rd_dna",
            conda_env="S_mip_rd-dna",
            root=mock_root_folder,
        ),
        "rna_api": MipAnalysisAPI(
            db=analysis_store_single_case,
            hk_api=housekeeper_api,
            tb_api=trailblazer_api,
            scout_api="scout_api",
            lims_api=mip_lims,
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
def mip_store_context(
    trailblazer_api, _store: Store, empty_housekeeper_api: HousekeeperAPI, mock_root_folder: Path
) -> dict:
    """Create a context to be used in testing mip store, this should be fused with mip_context above at later stages"""
    return {
        "mip_api": MipAnalysisAPI(
            db=_store,
            tb_api=trailblazer_api,
            hk_api=empty_housekeeper_api,
            scout_api=None,
            lims_api=None,
            script="None",
            pipeline="None",
            conda_env="None",
            root=mock_root_folder,
        ),
        "trailblazer_api": trailblazer_api,
        "housekeeper_api": empty_housekeeper_api,
        "status_db": _store,
    }
