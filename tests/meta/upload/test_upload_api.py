"""Test for upload API."""
import datetime as dt

from cg.meta.upload.upload_api import UploadAPI
from cg.models.cg_config import CGConfig
from cg.store.models import Family, Analysis

from tests.cli.workflow.conftest import tb_api
from tests.store_helpers import StoreHelpers


def test_mip_dna_update_uploaded_at(
    mip_dna_context: CGConfig, helpers: StoreHelpers, mip_dna_case: Family
):
    """Test setting uploaded at for a finished analysis."""
    # GIVEN an analysis that should be uploaded
    upload_api: UploadAPI = UploadAPI(
        config=mip_dna_context, analysis_api=mip_dna_context.meta_apis["analysis_api"]
    )
    dna_mip_analysis: Analysis = mip_dna_case.analyses[0]
    assert dna_mip_analysis.uploaded_at is None

    # WHEN setting the uploaded at
    upload_api.update_uploaded_at(analysis=dna_mip_analysis)

    # THEN the uploaded at should be set to a date
    assert isinstance(dna_mip_analysis.uploaded_at, dt.datetime)


def test_mip_rna_update_uploaded_at(
    mip_rna_context: CGConfig, helpers: StoreHelpers, mip_rna_case: Family
):
    """Test setting uploaded at for a finished analysis."""
    # GIVEN an analysis that should be uploaded
    upload_api: UploadAPI = UploadAPI(
        config=mip_rna_context, analysis_api=mip_rna_context.meta_apis["analysis_api"]
    )
    rna_mip_analysis: Analysis = mip_rna_case.analyses[0]
    assert rna_mip_analysis.uploaded_at is None

    # WHEN setting the uploaded at
    upload_api.update_uploaded_at(analysis=rna_mip_analysis)

    # THEN the uploaded at should be set to a date
    assert isinstance(rna_mip_analysis.uploaded_at, dt.datetime)
