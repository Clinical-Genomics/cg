from pathlib import Path

import pytest

from cg.apps.housekeeper.hk import HousekeeperAPI
from cg.apps.housekeeper.models import InputBundle
from cg.apps.tb import TrailblazerAPI
from cg.constants import Pipeline
from cg.meta.compress import CompressAPI
from cg.meta.workflow.mip_dna import MipDNAAnalysisAPI
from cg.meta.workflow.mip_rna import MipRNAAnalysisAPI
from cg.meta.workflow.prepare_fastq import PrepareFastqAPI
from cg.models.cg_config import CGConfig
from cg.store.api.find_business_data import FindBusinessDataHandler
from cg.store.api.status import StatusHandler
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
    analysis_family_single_case["data_analysis"] = str(Pipeline.MIP_RNA)
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
                data_analysis=Pipeline.MIP_DNA,
                internal_id=case_id,
                name=mip_case_ids[case_id]["name"],
            )
            sample = helpers.add_sample(
                store=_store,
                customer_id="cust000",
                application_tag="WGSA",
                application_type="wgs",
                gender="unknown",
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
    """Helper function to setup the necessary mocks for the decompression logics."""
    mocker.patch.object(StatusHandler, "cases_to_analyze")
    StatusHandler.cases_to_analyze.return_value = [case_to_analyze]

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

    mocker.patch.object(FindBusinessDataHandler, "are_all_flow_cells_on_disk")
    FindBusinessDataHandler.are_all_flow_cells_on_disk.return_value = True


@pytest.fixture
def scout_panel_output() -> str:
    return """##genome_build=37
##gene_panel=OMIM-AUTO,version=22.0,updated_at=2023-10-17,display_name=OMIM-AUTO
##gene_panel=PANELAPP-GREEN,version=6.0,updated_at=2023-10-19,display_name=PanelApp Green Genes
##contig=1
##contig=2
##contig=3
##contig=4
##contig=5
##contig=6
##contig=7
##contig=8
##contig=9
##contig=10
##contig=X
##contig=Y
##contig=MT
#chromosome	gene_start	gene_stop	hgnc_id	hgnc_symbol
1	568915	569121	44571	MTATP8P1
1	860260	879955	28706	SAMD11
2       162164549       162268228       16889   PSMD14
2       162272605       162282381       11590   TBR1
3       120315156       120321347       7699    NDUFB4
3       120347020       120401418       4892    HGD
4       185570767       185616117       26575   PRIMPOL
4       185676749       185747972       3569    ACSL1
5       473425  524447  11073   SLC9A3
5       892758  919472  12307   TRIP13
6       18224099        18265054        2768    DEK
6       19837617        19840915        5363    ID4
7       44256749        44374176        1461    CAMK2B
7       44646171        44748665        8124    OGDH
8       22993101        23021543        11907   TNFRSF10D
8       23047965        23082639        11904   TNFRSF10A
9       35099888        35103154        14559   STOML2
9       35161999        35405335        12566   UNC13B
10      23481256        23483181        23734   PTF1A
10      25305587        25315593        26160   THNSL1
X       154719776       154899605       18308   TMLHE
X       155110956       155173433       11486   VAMP7
Y       6778727 6959724 18502   TBL1Y
Y       14813160        14972764        12633   USP9Y
MT      577     647     7481    MT-TF
MT      648     1601    7470    MT-RNR1"""
