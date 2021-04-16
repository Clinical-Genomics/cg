import copy
import datetime as dt
from pathlib import Path
from typing import List

import pytest
from ruamel.yaml import YAML

from cg.apps.housekeeper.hk import HousekeeperAPI
from cg.constants import Pipeline
from cg.meta.workflow.mip_dna import MipDNAAnalysisAPI
from cg.meta.workflow.mip_rna import MipRNAAnalysisAPI
from cg.models.cg_config import CGConfig
from tests.store_helpers import StoreHelpers


@pytest.fixture(name="mip_case_ids")
def fixture_mip_case_ids() -> dict:
    """Dictionary of case ids, connected samples, their name and if they should fail (textbook or not)"""

    return {
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

    for case, value in mip_case_ids.items():
        if value["textbook"]:
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
        else:
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


@pytest.fixture(name="rna_mip_context")
def fixture_rna_mip_context(
    cg_context: CGConfig,
    analysis_family_single_case: dict,
    helpers: StoreHelpers,
    apptag_rna: str,
    case_id: str,
    housekeeper_api: HousekeeperAPI,
) -> CGConfig:
    cg_context.housekeeper_api_ = housekeeper_api
    analysis_family_single_case["data_analysis"] = str(Pipeline.MIP_RNA)
    if not cg_context.status_db.family(case_id):
        helpers.ensure_case_from_dict(
            cg_context.status_db, case_info=analysis_family_single_case, app_tag=apptag_rna
        )
    cg_context.meta_apis["analysis_api"] = MipRNAAnalysisAPI(cg_context)
    return cg_context


@pytest.fixture(name="dna_mip_context")
def fixture_dna_mip_context(
    cg_context: CGConfig, helpers: StoreHelpers, mip_case_ids: dict, housekeeper_api: HousekeeperAPI
) -> CGConfig:
    _store = cg_context.status_db
    cg_context.housekeeper_api_ = housekeeper_api

    # Add apptag to db
    helpers.ensure_application_version(store=_store, application_tag="WGSA", application_type="wgs")

    # Add sample, cases and relationships to db

    for case_id in mip_case_ids:
        if not _store.family(case_id):
            case_obj = helpers.add_case(
                store=_store,
                internal_id=case_id,
                case_id=mip_case_ids[case_id]["name"],
            )
            sample = helpers.add_sample(
                store=_store,
                sample=mip_case_ids[case_id]["internal_id"],
                data_analysis=Pipeline.MIP_DNA,
                customer_name="cust000",
                application_tag="WGSA",
                application_type="wgs",
                gender="unknown",
            )
            helpers.add_relationship(store=_store, sample=sample, case=case_obj, status="affected")
    cg_context.meta_apis["analysis_api"] = MipDNAAnalysisAPI(cg_context)
    return cg_context
