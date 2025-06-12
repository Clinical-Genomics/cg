"""Test for upload API."""

import datetime as dt

import pytest

from cg.meta.upload.upload_api import UploadAPI
from cg.models.cg_config import CGConfig
from cg.store.models import Analysis, Case
from tests.cli.workflow.conftest import tb_api
from tests.cli.workflow.mip.conftest import (
    mip_case_id,
    mip_case_ids,
    mip_dna_context,
    mip_rna_context,
)
from tests.store_helpers import StoreHelpers


@pytest.mark.freeze_time
def test_mip_dna_update_uploaded_at(
    mip_dna_context: CGConfig, mip_dna_case: Case, helpers: StoreHelpers
):
    """Test setting uploaded at for a finished analysis."""
    # GIVEN an analysis that should be uploaded
    upload_api: UploadAPI = UploadAPI(
        config=mip_dna_context, analysis_api=mip_dna_context.meta_apis["analysis_api"]
    )
    dna_mip_analysis: Analysis = helpers.add_analysis(
        store=mip_dna_context.status_db,
        case=mip_dna_case,
        completed_at=dt.datetime.now(),
        uploaded_at=None,
    )

    # WHEN setting the uploaded at
    upload_api.update_uploaded_at(analysis=dna_mip_analysis)

    # THEN the uploaded at should be set to a date
    assert dna_mip_analysis.uploaded_at == dt.datetime.now()


def test_mip_rna_update_uploaded_at(mip_rna_context: CGConfig, mip_rna_analysis: Analysis):
    """Test setting uploaded at for a finished analysis."""
    # GIVEN an analysis that should be uploaded
    upload_api: UploadAPI = UploadAPI(
        config=mip_rna_context, analysis_api=mip_rna_context.meta_apis["analysis_api"]
    )

    assert mip_rna_analysis.uploaded_at is None

    # WHEN setting the uploaded at
    upload_api.update_uploaded_at(analysis=mip_rna_analysis)

    # THEN the uploaded at should be set to a date
    assert isinstance(mip_rna_analysis.uploaded_at, dt.datetime)
