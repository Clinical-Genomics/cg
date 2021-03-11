"""Unit tests for updating existing records in status-db tables"""

import mock
import datetime as dt

import cg.store.api.update

from tests.conftest import FAKE_NOW

UPLOADED_TO_VOGUE_DATE = dt.datetime(2021, 3, 1)
OLD_DATE = dt.datetime(2020, 12, 31)


@mock.patch("cg.store.Store")
@mock.patch("cg.store.models.Analysis")
def test_update_analysis_uploaded_to_vogue_date_given_date(mock_store, mock_analysis):
    """tests updating the uploaded_to_vogue field of a record in the analysis table"""

    # GIVEN an analysis object with no uploaded_to_vogue date

    # WHEN setting the uploaded to vogue date to a specific date
    vogue_upload_date = UPLOADED_TO_VOGUE_DATE
    result = cg.store.api.update.update_analysis_uploaded_to_vogue_date(
        mock_store, mock_analysis, vogue_upload_date
    )

    # THEN the analysis object should have a vogue_uploaded_date set to vogue_upload_date
    assert result.uploaded_to_vogue_at == vogue_upload_date


@mock.patch("cg.store.Store")
@mock.patch("cg.store.models.Analysis")
def test_update_analysis_uploaded_to_vogue_date_none_date(mock_store, mock_analysis):
    """tests updating the uploaded_to_vogue field of a record in the analysis table"""

    # GIVEN an analysis object with an existing uploaded_to_vogue date
    mock_analysis.uploaded_to_vogue_date = OLD_DATE

    # WHEN setting the uploaded to vogue date to a specific date
    vogue_upload_date = None
    result = cg.store.api.update.update_analysis_uploaded_to_vogue_date(
        mock_store, mock_analysis, vogue_upload_date
    )

    # THEN the analysis object should have a vogue_uploaded_date set to None
    assert result.uploaded_to_vogue_at is None


@mock.patch.object(
    cg.store.api.update.update_analysis_uploaded_to_vogue_date, "__defaults__", (FAKE_NOW,)
)
@mock.patch("cg.store.Store")
@mock.patch("cg.store.models.Analysis")
def test_update_analysis_uploaded_to_vogue_date_now(mock_store, mock_analysis, patch_datetime_now):
    """tests updating the uploaded_to_vogue field of a record in the analysis table"""

    # GIVEN an analysis object with no uploaded_to_vogue date

    # WHEN setting the uploaded to vogue date without specifying a date
    result = cg.store.api.update.update_analysis_uploaded_to_vogue_date(mock_store, mock_analysis)

    # THEN the analysis object should have a vogue_uploaded_date set to the default value dt.datetime.now()
    assert result.uploaded_to_vogue_at == FAKE_NOW
