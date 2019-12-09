"""Test for UploadVogueAPI"""

import json

from cg.meta.upload.vogue import UploadVogueAPI


def test_load_genotype(genotypeapi, vogueapi, genotype_return_sample,
                       genotype_return_sample_analysis, mocker):

    """Test load_genotype"""

    # GIVEN UploadVogueAPI and a genotype_return_sample

    # WHEN running load_genotype
    mocker.patch.object(vogueapi, 'load_genotype_data')
    mocker.patch.object(genotypeapi, 'export_sample')
    mocker.patch.object(genotypeapi, 'export_sample_analysis')

    genotypeapi.export_sample.return_value = genotype_return_sample
    genotypeapi.export_sample_analysis.return_value = genotype_return_sample_analysis
    upploadvogueapi = UploadVogueAPI(genotype_api=genotypeapi, vogue_api=vogueapi)
    upploadvogueapi.load_genotype(days='1')

    # THEN vogueapi.load_genotype will be called once for each sample in genotype_return_value
    samples = json.loads(genotype_return_sample)
    call_list = vogueapi.load_genotype_data.call_args_list

    assert vogueapi.load_genotype_data.call_count == 4
    for call in call_list:
        assert call[0][0]['_id'] in samples.keys()
