"""Test for UploadVogueAPI"""

import json

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
    samples = json.loads(genotype_return["sample"])
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
