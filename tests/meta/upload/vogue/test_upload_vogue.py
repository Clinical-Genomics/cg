"""Test for UploadVogueAPI"""

import mock

from cg.constants.constants import FileFormat
from cg.io.controller import ReadStream
from cg.meta.upload.vogue import UploadVogueAPI


def test_load_genotype(genotype_api, vogue_api, genotype_return, mocker, store):
    """Test load_genotype"""

    # GIVEN UploadVogueAPI and a genotype_return_sample

    # WHEN running load_genotype
    mocker.patch.object(vogue_api, "load_genotype_data")
    mocker.patch.object(genotype_api, "export_sample")
    mocker.patch.object(genotype_api, "export_sample_analysis")

    genotype_api.export_sample.return_value = genotype_return["sample"]
    genotype_api.export_sample_analysis.return_value = genotype_return["sample_analysis"]
    upload_vogue_api = UploadVogueAPI(genotype_api=genotype_api, vogue_api=vogue_api, store=store)
    upload_vogue_api.load_genotype(days="1")

    # THEN vogueapi.load_genotype will be called once for each sample in genotype_return_value
    samples = ReadStream.get_content_from_stream(
        file_format=FileFormat.JSON, stream=genotype_return["sample"]
    )
    call_list = vogue_api.load_genotype_data.call_args_list

    assert vogue_api.load_genotype_data.call_count == 4
    for call in call_list:
        assert call[0][0]["_id"] in samples.keys()


def test_load_apptags(vogue_api, genotype_api, store, mocker):
    """Test load application tags"""
    # GIVEN UploadVogueAPI and a set of application tags
    apptags = store.applications().apptag_list

    mocker.patch.object(vogue_api, "load_apptags")
    upload_vogue_api = UploadVogueAPI(genotype_api=genotype_api, vogue_api=vogue_api, store=store)

    # WHEN running load_apptags
    upload_vogue_api.load_apptags()

    # THEN load_apptags is called with the apptags inside upload_vogue_api
    vogue_api.load_apptags.assert_called_with(apptags)


@mock.patch("cg.store.Store")
@mock.patch("cg.apps.vogue.VogueAPI")
@mock.patch("cg.apps.gt.GenotypeAPI")
@mock.patch("cg.store.models.Analysis")
def test_update_analysis_uploaded_to_vogue_date_given_date(
    mock_analysis, mock_genotype_api, mock_vogue_api, mock_store, uploaded_to_vogue_date
):
    """tests updating the uploaded_to_vogue_at field of a record in the analysis table"""

    # GIVEN an analysis object with no uploaded_to_vogue date

    # WHEN setting the uploaded to vogue date to a specific date
    result = UploadVogueAPI(
        genotype_api=mock_genotype_api, vogue_api=mock_vogue_api, store=mock_store
    ).update_analysis_uploaded_to_vogue_date(mock_analysis, uploaded_to_vogue_date)

    # THEN the analysis object should have a vogue_uploaded_date set to vogue_upload_date
    assert result.uploaded_to_vogue_at == uploaded_to_vogue_date


@mock.patch("cg.store.Store")
@mock.patch("cg.apps.vogue.VogueAPI")
@mock.patch("cg.apps.gt.GenotypeAPI")
@mock.patch("cg.store.models.Analysis")
def test_update_analysis_uploaded_to_vogue_date_now(
    mock_analysis, mock_genotype_api, mock_vogue_api, mock_store, timestamp_now
):
    """tests updating the uploaded_to_vogue field of a record in the analysis table"""

    # GIVEN an analysis object with no uploaded_to_vogue date

    # WHEN setting the uploaded to vogue date without specifying a date
    with mock.patch.object(
        UploadVogueAPI.update_analysis_uploaded_to_vogue_date,
        "__defaults__",
        (timestamp_now,),
    ):
        result = UploadVogueAPI(
            mock_genotype_api, mock_vogue_api, mock_store
        ).update_analysis_uploaded_to_vogue_date(mock_analysis)

    # THEN the analysis object should have a vogue_uploaded_date set to the default value
    # dt.datetime.now()
    assert result.uploaded_to_vogue_at == timestamp_now
