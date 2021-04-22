"""Unit tests for updating existing records in status-db tables"""

import datetime as dt

import mock

# import cg.store.api.update
import cg.store.api.update
from cg.meta.upload.vogue import UploadVogueAPI

UPLOADED_TO_VOGUE_DATE = dt.datetime(2021, 3, 1)
OLD_DATE = dt.datetime(2020, 12, 31)


@mock.patch("cg.store.Store")
@mock.patch("cg.apps.vogue.VogueAPI")
@mock.patch("cg.apps.gt.GenotypeAPI")
@mock.patch("cg.store.models.Analysis")
def test_update_analysis_uploaded_to_vogue_date_given_date(
    mock_analysis, mock_genotype_api, mock_vogue_api, mock_store
):
    """tests updating the uploaded_to_vogue_at field of a record in the analysis table"""

    # GIVEN an analysis object with no uploaded_to_vogue date

    # WHEN setting the uploaded to vogue date to a specific date
    result = UploadVogueAPI(
        genotype_api=mock_genotype_api, vogue_api=mock_vogue_api, store=mock_store
    ).update_analysis_uploaded_to_vogue_date(mock_analysis, UPLOADED_TO_VOGUE_DATE)

    # THEN the analysis object should have a vogue_uploaded_date set to vogue_upload_date
    assert result.uploaded_to_vogue_at == UPLOADED_TO_VOGUE_DATE


@mock.patch("cg.store.Store")
@mock.patch("cg.apps.vogue.VogueAPI")
@mock.patch("cg.apps.gt.GenotypeAPI")
@mock.patch("cg.store.models.Analysis")
def test_update_analysis_uploaded_to_vogue_date_none_date(
    mock_analysis, mock_genotype_api, mock_vogue_api, mock_store
):
    """tests updating the uploaded_to_vogue field of a record in the analysis table"""

    # GIVEN an analysis object with an existing uploaded_to_vogue date
    mock_analysis.analyses.uploaded_to_vogue_at = OLD_DATE

    # WHEN setting the uploaded to vogue date to None
    result = UploadVogueAPI(
        genotype_api=mock_genotype_api, vogue_api=mock_vogue_api, store=mock_store
    ).update_analysis_uploaded_to_vogue_date(mock_analysis, vogue_upload_date=None)

    # THEN the analysis object should have a vogue_uploaded_date set to None
    assert result.uploaded_to_vogue_at is None


@mock.patch("cg.store.Store")
@mock.patch("cg.apps.vogue.VogueAPI")
@mock.patch("cg.apps.gt.GenotypeAPI")
@mock.patch("cg.store.models.Analysis")
def test_update_analysis_uploaded_to_vogue_date_now(
    mock_analysis, mock_genotype_api, mock_vogue_api, mock_store, timestamp_today
):
    """tests updating the uploaded_to_vogue field of a record in the analysis table"""

    # GIVEN an analysis object with no uploaded_to_vogue date

    # WHEN setting the uploaded to vogue date without specifying a date
    with mock.patch.object(
        UploadVogueAPI.update_analysis_uploaded_to_vogue_date,
        "__defaults__",
        (timestamp_today,),
    ):

        result = UploadVogueAPI(
            mock_genotype_api, mock_vogue_api, mock_store
        ).update_analysis_uploaded_to_vogue_date(mock_analysis)

    # THEN the analysis object should have a vogue_uploaded_date set to the default value
    # dt.datetime.now()
    assert result.uploaded_to_vogue_at == timestamp_today
