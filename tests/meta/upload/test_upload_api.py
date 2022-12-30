"""Test for upload API."""
import datetime as dt

from cg.meta.upload.upload_api import UploadAPI
from cg.models.cg_config import CGConfig
from cg.store.models import Family, Analysis
from tests.cli.workflow.conftest import tb_api
from tests.store_helpers import StoreHelpers


def test_update_uploaded_at(dna_mip_context: CGConfig, helpers: StoreHelpers, mip_case: Family):
    """Test setting uploaded at for a finished analysis."""
    # GIVEN an analysis that should be uploaded
    upload_api: UploadAPI = UploadAPI(
        config=dna_mip_context, analysis_api=dna_mip_context.meta_apis["analysis_api"]
    )
    mip_analysis: Analysis = mip_case.analyses[0]
    assert mip_analysis.uploaded_at is None

    # WHEN setting the uploaded at
    upload_api.update_uploaded_at(analysis=mip_analysis)

    # THEN the uploaded at should be set to a date
    assert isinstance(mip_analysis.uploaded_at, dt.datetime)
