from cg.cli.upload.utils import get_scout_api_by_case, get_scout_api_by_genome_build
from cg.constants import Workflow
from cg.models.cg_config import CGConfig
from cg.store.models import Case
from tests.store_helpers import StoreHelpers


def test_get_scout_api_by_case_nallo(upload_context: CGConfig, helpers: StoreHelpers):

    # GIVEN a Nallo case
    nallo_case: Case = helpers.ensure_case(
        store=upload_context.status_db, data_analysis=Workflow.NALLO
    )

    # WHEN getting the corresponding ScoutAPI
    scout_api = get_scout_api_by_case(cg_config=upload_context, case_id=nallo_case.internal_id)

    # THEN the ScoutAPI should be towards the hg38 instance
    assert scout_api == upload_context.scout_api_38


def test_get_scout_api_by_case_raredisease(upload_context: CGConfig, helpers: StoreHelpers):

    # GIVEN a Nallo case
    nallo_case: Case = helpers.ensure_case(
        store=upload_context.status_db, data_analysis=Workflow.RAREDISEASE
    )

    # WHEN getting the corresponding ScoutAPI
    scout_api = get_scout_api_by_case(cg_config=upload_context, case_id=nallo_case.internal_id)

    # THEN the ScoutAPI should be towards the hg38 instance
    assert scout_api == upload_context.scout_api_38


def test_get_scout_api_by_case_37(upload_context: CGConfig, helpers: StoreHelpers):

    # GIVEN a MIP-DNA case
    nallo_case: Case = helpers.ensure_case(
        store=upload_context.status_db, data_analysis=Workflow.MIP_DNA
    )

    # WHEN getting the corresponding ScoutAPI
    scout_api = get_scout_api_by_case(cg_config=upload_context, case_id=nallo_case.internal_id)

    # THEN the ScoutAPI should be towards the hg37 instance
    assert scout_api == upload_context.scout_api_37


def test_get_scout_api_by_reference_genome_hg19(upload_context: CGConfig):
    # WHEN getting the corresponding ScoutAPI for hg19
    scout_api = get_scout_api_by_genome_build(cg_config=upload_context, genome_build="hg19")

    # THEN the ScoutAPI should be towards the hg37 instance
    assert scout_api == upload_context.scout_api_37


def test_get_scout_api_by_reference_genome_hg38(upload_context: CGConfig):
    # WHEN getting the corresponding ScoutAPI for hg38
    scout_api = get_scout_api_by_genome_build(cg_config=upload_context, genome_build="hg38")

    # THEN the ScoutAPI should be towards the hg38 instance
    assert scout_api == upload_context.scout_api_38
