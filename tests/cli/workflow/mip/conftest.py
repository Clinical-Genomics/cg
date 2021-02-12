import copy
import datetime as dt
from pathlib import Path

import pytest

from cg.apps.crunchy import CrunchyAPI
from cg.apps.housekeeper.hk import HousekeeperAPI
from cg.apps.tb import TrailblazerAPI
from cg.apps.tb.models import TrailblazerAnalysis as tb_Analysis
from cg.constants import Pipeline
from cg.meta.compress.compress import CompressAPI
from cg.meta.workflow.mip import MipAnalysisAPI
from cg.meta.workflow.prepare_fastq import PrepareFastqAPI
from cg.store import Store
from ruamel.yaml import YAML
from tests.mocks.limsmock import MockLimsAPI


@pytest.fixture(name="mip_lims")
def fixture_mip_lims() -> MockLimsAPI:
    mip_lims = MockLimsAPI({})
    return mip_lims


@pytest.fixture(name="mock_mip_script")
def fixture_mock_mip_script() -> str:
    return "echo"


@pytest.fixture
def mock_root_folder(project_dir: Path) -> str:
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

    for case_id in mip_case_ids:
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


@pytest.fixture(name="mip_rna_conda_env_name")
def fixture_mip_rna_conda_env_name() -> str:
    return "S_mip_rd-rna"


@pytest.fixture(name="mip_dna_conda_env_name")
def fixture_mip_dna_conda_env_name() -> str:
    return "S_mip_rd-dna"


@pytest.fixture(name="mip_dna_pipeline")
def fixture_mip_dna_pipeline() -> str:
    return "analyse rd_dna"


@pytest.fixture(name="mip_rna_pipeline")
def fixture_mip_rna_pipeline() -> str:
    return "analyse rd_rna"


@pytest.fixture(scope="function", name="analysis_store_rna_case")
def fixture_analysis_store_rna_case(
    base_store: Store, analysis_family_single_case: dict, apptag_rna: str, helpers
) -> Store:
    """Setup a store instance with a single ind RNA case for testing analysis API"""
    analysis_family_single_case["data_analysis"] = str(Pipeline.MIP_RNA)
    helpers.ensure_case_from_dict(
        base_store, case_info=analysis_family_single_case, app_tag=apptag_rna
    )

    yield base_store


@pytest.fixture(name="rna_mip_context")
def fixture_rna_mip_context(
    analysis_store_rna_case: Store,
    trailblazer_api: TrailblazerAPI,
    housekeeper_api: HousekeeperAPI,
    mip_lims: MockLimsAPI,
    mock_root_folder: str,
    mock_mip_script: str,
    mip_rna_conda_env_name: str,
    mip_dna_conda_env_name: str,
    mip_rna_pipeline: str,
):
    rna_mip_context = {
        "rna_api": MipAnalysisAPI(
            db=analysis_store_rna_case,
            hk_api=housekeeper_api,
            tb_api=trailblazer_api,
            scout_api="scout_api",
            lims_api=mip_lims,
            script=mock_mip_script,
            pipeline=mip_rna_pipeline,
            conda_env=mip_rna_conda_env_name,
            root=mock_root_folder,
        ),
        "mip-rd-rna": {
            "conda_env": mip_rna_conda_env_name,
            "mip_config": "config.yaml",
            "pipeline": mip_rna_pipeline,
            "root": mock_root_folder,
            "script": mock_mip_script,
        },
    }
    return rna_mip_context


@pytest.fixture(name="crunchy_config")
def fixture_crunchy_config(crunchy_config_dict) -> dict:
    """Returns a config for CrunchyAPI"""
    return crunchy_config_dict


@pytest.fixture(name="crunchy")
def fixture_crunchy(crunchy_config_dict) -> CrunchyAPI:
    """Returns CrunchyAPI"""
    crunchy_api = CrunchyAPI(crunchy_config_dict)
    return crunchy_api


@pytest.fixture(name="compress")
def fixture_compress(housekeeper_api, crunchy) -> CompressAPI:
    """Returns CompressAPI"""
    compress_api = CompressAPI(hk_api=housekeeper_api, crunchy_api=crunchy)
    return compress_api


@pytest.fixture(name="dna_mip_context")
def fixture_dna_mip_context(
    analysis_store_single_case: Store,
    trailblazer_api: TrailblazerAPI,
    housekeeper_api: HousekeeperAPI,
    crunchy: CrunchyAPI,
    compress: CompressAPI,
    crunchy_config: dict,
    mip_lims: MockLimsAPI,
    mock_root_folder: str,
    mock_mip_script: str,
    mip_rna_conda_env_name: str,
    mip_dna_conda_env_name: str,
    mip_dna_pipeline: str,
):
    dna_mip_context = {
        "dna_api": MipAnalysisAPI(
            db=analysis_store_single_case,
            hk_api=housekeeper_api,
            tb_api=trailblazer_api,
            scout_api="scout_api",
            lims_api=mip_lims,
            script=mock_mip_script,
            pipeline=mip_dna_pipeline,
            conda_env=mip_dna_conda_env_name,
            root=mock_root_folder,
        ),
        "crunchy_api": CrunchyAPI(crunchy_config),
        "compress_api": CompressAPI(hk_api=housekeeper_api, crunchy_api=crunchy),
        "prepare_fastq_api": PrepareFastqAPI(
            store=analysis_store_single_case, compress_api=compress
        ),
        "mip-rd-dna": {
            "conda_env": mip_dna_conda_env_name,
            "mip_config": "config.yaml",
            "pipeline": mip_dna_pipeline,
            "root": mock_root_folder,
            "script": mock_mip_script,
        },
    }
    return dna_mip_context


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
