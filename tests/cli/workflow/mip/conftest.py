from pathlib import Path

import pytest

from cg.apps.housekeeper.hk import HousekeeperAPI
from cg.apps.housekeeper.models import InputBundle
from cg.apps.scout.scoutapi import ScoutAPI
from cg.apps.tb import TrailblazerAPI
from cg.constants import Workflow
from cg.constants.subject import Sex
from cg.meta.compress import CompressAPI
from cg.meta.workflow.mip_dna import MipDNAAnalysisAPI
from cg.meta.workflow.mip_rna import MipRNAAnalysisAPI
from cg.meta.workflow.prepare_fastq import PrepareFastqAPI
from cg.models.cg_config import CGConfig
from cg.store.crud.read import ReadHandler
from cg.store.models import Case
from tests.store_helpers import StoreHelpers


@pytest.fixture
def mip_dna_config_path() -> str:
    return "tests/fixtures/apps/mip/dna/case_config.yaml"


@pytest.fixture
def mip_case_id() -> str:
    return "yellowhog"


@pytest.fixture
def mip_case_id_non_existing() -> str:
    return "this_case_id_does_not_exist"


@pytest.fixture
def mip_case_ids(mip_case_id: str) -> dict:
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


@pytest.fixture
def mip_case_dirs(mip_case_ids: dict, project_dir: Path) -> dict:
    """Create case directories and return a dictionary of the tmpdir paths"""

    mip_case_dirs = {}

    for case in mip_case_ids:
        case_dir = Path(project_dir / "cases" / case)
        case_dir.mkdir(exist_ok=True, parents=True)
        mip_case_dirs[case] = case_dir

    return mip_case_dirs


@pytest.fixture
def mip_hermes_dna_deliverables_response_data(
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


@pytest.fixture
def mip_rna_context(
    cg_context: CGConfig,
    analysis_family_single_case: dict,
    helpers: StoreHelpers,
    apptag_rna: str,
    case_id: str,
    housekeeper_api: HousekeeperAPI,
    tb_api,
) -> CGConfig:
    cg_context.housekeeper_api_ = housekeeper_api
    cg_context.trailblazer_api_ = tb_api
    analysis_family_single_case["data_analysis"] = Workflow.MIP_RNA
    if not cg_context.status_db.get_case_by_internal_id(internal_id=case_id):
        helpers.ensure_case_from_dict(
            cg_context.status_db, case_info=analysis_family_single_case, app_tag=apptag_rna
        )
    cg_context.meta_apis["analysis_api"] = MipRNAAnalysisAPI(cg_context)
    return cg_context


@pytest.fixture
def mip_dna_context(
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
    helpers.ensure_application_version(store=_store, application_tag="WGSA", prep_category="wgs")

    # Add sample, cases and relationships to db

    for case_id in mip_case_ids:
        if not _store.get_case_by_internal_id(internal_id=case_id):
            case_obj = helpers.add_case(
                store=_store,
                data_analysis=Workflow.MIP_DNA,
                internal_id=case_id,
                name=mip_case_ids[case_id]["name"],
            )
            sample = helpers.add_sample(
                store=_store,
                application_tag="WGSA",
                application_type="wgs",
                customer_id="cust000",
                sex=Sex.UNKNOWN,
            )
            helpers.add_relationship(store=_store, sample=sample, case=case_obj, status="affected")
    cg_context.meta_apis["analysis_api"] = mip_analysis_api
    return cg_context


def setup_mocks(
    mocker,
    can_at_least_one_sample_be_decompressed: bool = False,
    case_to_analyze: Case = None,
    decompress_spring: bool = False,
    has_latest_analysis_started: bool = False,
    is_spring_decompression_needed: bool = False,
    is_spring_decompression_running: bool = False,
) -> None:
    """Helper function to set up the necessary mocks for the decompression logics."""
    mocker.patch.object(ReadHandler, "cases_to_analyse")
    ReadHandler.cases_to_analyse.return_value = [case_to_analyze]

    mocker.patch.object(PrepareFastqAPI, "is_spring_decompression_needed")
    PrepareFastqAPI.is_spring_decompression_needed.return_value = is_spring_decompression_needed

    mocker.patch.object(TrailblazerAPI, "has_latest_analysis_started")
    TrailblazerAPI.has_latest_analysis_started.return_value = has_latest_analysis_started

    mocker.patch.object(PrepareFastqAPI, "can_at_least_one_sample_be_decompressed")
    PrepareFastqAPI.can_at_least_one_sample_be_decompressed.return_value = (
        can_at_least_one_sample_be_decompressed
    )

    mocker.patch.object(CompressAPI, "decompress_spring")
    CompressAPI.decompress_spring.return_value = decompress_spring

    mocker.patch.object(PrepareFastqAPI, "is_spring_decompression_running")
    PrepareFastqAPI.is_spring_decompression_running.return_value = is_spring_decompression_running

    mocker.patch.object(PrepareFastqAPI, "add_decompressed_fastq_files_to_housekeeper")
    PrepareFastqAPI.add_decompressed_fastq_files_to_housekeeper.return_value = None

    mocker.patch.object(MipDNAAnalysisAPI, "get_panel_bed")
    MipDNAAnalysisAPI.get_panel_bed.return_value = "a_string"

    mocker.patch.object(
        ScoutAPI,
        "export_managed_variants",
        return_value=["a str"],
    )

    mocker.patch.object(ReadHandler, "are_all_flow_cells_on_disk")
    ReadHandler.are_all_flow_cells_on_disk.return_value = True
