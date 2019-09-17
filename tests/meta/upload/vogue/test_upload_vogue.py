"""Test for UploadVogueAPI"""

import json

from cg.meta.upload.vogue import UploadVogueAPI


def test_load_genotype(genotypeapi, vogueapi, find_basic, genotype_return_value, mocker):

    """Test load_genotype"""

    # GIVEN UploadVogueAPI and a genotype_return_value

    # WHEN running load_genotype
    mocker.patch.object(vogueapi, 'load_genotype')
    mocker.patch.object(genotypeapi, 'get_trending')

    genotypeapi.get_trending.return_value = genotype_return_value
    upploadvogueapi = UploadVogueAPI(genotype_api=genotypeapi, vogue_api=vogueapi,
                                     find_basic=find_basic)
    upploadvogueapi.load_genotype(days='1')

    # THEN vogueapi.load_genotype will be called once for each sample in genotype_return_value
    samples = json.loads(genotype_return_value)
    call_list = vogueapi.load_genotype.call_args_list

    assert vogueapi.load_genotype.call_count == 4
    for call in call_list:
        assert call[0][0]['_id'] in samples.keys()


def test_load_apptags(vogueapi, genotypeapi, find_basic, mocker):

    """Test load application tags"""
    # GIVEN UploadVogueAPI and a set of application tags
    apptags = find_basic.applications().apptag_list

    mocker.patch.object(vogueapi, 'load_apptags')
    upploadvogueapi = UploadVogueAPI(genotype_api=genotypeapi, vogue_api=vogueapi,
                                     find_basic=find_basic)

    # WHEN running load_apptags
    upploadvogueapi.load_apptags()

    # THEN load_apptags is called with the apptags inside upploadvogueapi
    vogueapi.load_apptags.assert_called_with(apptags)
