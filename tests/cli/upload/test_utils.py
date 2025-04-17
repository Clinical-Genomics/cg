from cg.cli.upload.utils import get_scout_api
from cg.constants import Workflow
from cg.models.cg_config import CGConfig
from cg.store.models import Case
from tests.store_helpers import StoreHelpers


def test_get_scout_api_38(upload_context: CGConfig, helpers: StoreHelpers):

    # GIVEN a Nallo case
    nallo_case: Case = helpers.ensure_case(
        store=upload_context.status_db, data_analysis=Workflow.NALLO
    )

    # WHEN getting the corresponding ScoutAPI
    scout_api = get_scout_api(cg_config=upload_context, case_id=nallo_case.internal_id)

    # THEN the ScoutAPI should be towards the hg38 instance
    assert scout_api == upload_context.scout_api_38


def test_get_scout_api_37(upload_context: CGConfig, helpers: StoreHelpers):

    # GIVEN a MIP-DNA case
    nallo_case: Case = helpers.ensure_case(
        store=upload_context.status_db, data_analysis=Workflow.MIP_DNA
    )

    # WHEN getting the corresponding ScoutAPI
    scout_api = get_scout_api(cg_config=upload_context, case_id=nallo_case.internal_id)

    # THEN the ScoutAPI should be towards the hg37 instance
    assert scout_api == upload_context.scout_api_37
