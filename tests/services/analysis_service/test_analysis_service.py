from datetime import datetime
from unittest.mock import Mock

from cg.constants import Workflow
from cg.services.analysis_service.analysis_service import AnalysisService
from cg.store.models import Analysis
from cg.store.store import Store
from tests.store_helpers import StoreHelpers


def test_get_analyses_to_upload_for_workflow(
    helpers: StoreHelpers, base_store: Store, timestamp_now: datetime
):
    # GIVEN an analysis service and a store with analyses to upload and not to upload
    analysis_upload: Analysis = helpers.add_analysis(
        store=base_store,
        uploaded_at=None,
        upload_started=None,
        workflow=Workflow.RAW_DATA,
        completed_at=timestamp_now,
    )
    new_case = helpers.add_case(store=base_store, name="no_upload_case")
    analysis_no_upload: Analysis = helpers.add_analysis(
        store=base_store,
        case=new_case,
        uploaded_at=timestamp_now,
        upload_started=None,
        workflow=Workflow.RAW_DATA,
        completed_at=timestamp_now,
    )
    analysis_service = AnalysisService(analysis_client=Mock(), status_db=base_store)

    # WHEN getting analyses to upload
    analyses: list[Analysis] = analysis_service.get_analyses_to_upload_for_workflow(
        workflow=Workflow.RAW_DATA
    )

    # THEN only the analyses to upload should be returned
    assert analyses == [analysis_upload]
    assert analysis_no_upload not in analyses
