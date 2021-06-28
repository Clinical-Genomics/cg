from pathlib import Path

import pytest

from cg.apps.housekeeper.hk import HousekeeperAPI
from cg.apps.housekeeper.models import InputBundle
from cg.constants import Pipeline
from cg.meta.workflow.mip_dna import MipDNAAnalysisAPI
from cg.meta.workflow.mip_rna import MipRNAAnalysisAPI
from cg.models.cg_config import CGConfig
from tests.store_helpers import StoreHelpers


@pytest.fixture(name="mip_case_id")
def fixture_mip_case_id() -> str:
    return "yellowhog"


@pytest.fixture(name="mip_case_id_non_existing")
def fixture_mip_case_id_non_existing() -> str:
    return "this_case_id_does_not_exist"


@pytest.fixture(name="mip_case_ids")
def fixture_mip_case_ids(mip_case_id: str) -> dict:
    """Dictionary of case ids, connected samples, their name and if they should fail (textbook or not)"""

    return {
        mip_case_id: {
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


@pytest.fixture(name="mip_hermes_dna_deliverables_response_data")
def fixture_mip_dna_hermes_deliverables_response_data(
    create_multiqc_html_file,
    create_multiqc_json_file,
    mip_case_id,
    timestamp_yesterday,
) -> InputBundle:
    return InputBundle(
        **{
            "files": [
                {
                    "path": create_multiqc_json_file.as_posix(),
                    "tags": ["multiqc-json", mip_case_id, "mip-dna"],
                },
                {
                    "path": create_multiqc_html_file.as_posix(),
                    "tags": ["multiqc-html", mip_case_id, "mip-dna"],
                },
            ],
            "created": timestamp_yesterday,
            "name": mip_case_id,
        }
    )


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
    cg_context: CGConfig,
    helpers: StoreHelpers,
    mip_case_ids: dict,
    real_housekeeper_api: HousekeeperAPI,
    tb_api,
) -> CGConfig:
    _store = cg_context.status_db
    cg_context.housekeeper_api_ = real_housekeeper_api
    cg_context.trailblazer_api_ = tb_api
    mip_analysis_api = MipDNAAnalysisAPI(config=cg_context)

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
    cg_context.meta_apis["analysis_api"] = mip_analysis_api
    return cg_context
