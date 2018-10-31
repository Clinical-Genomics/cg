from cg.meta.upload.scoutapi import UploadScoutAPI
from cg.store import Store


def test_generate_config_adds_rank_model_version(analysis: Store.Analysis, upload_scout_api:
UploadScoutAPI):

    # GIVEN a status db and hk with an analysis
    assert analysis

    # WHEN generating the scout config for the analysis
    result_data = upload_scout_api.generate_config(analysis)

    # THEN the config should contain the rank model version used
    assert result_data['human_genome_build']
    assert result_data['rank_model_version']


def test_generate_config_adds_(analysis: Store.Analysis, upload_scout_api: UploadScoutAPI):

    # GIVEN a status db and hk with an analysis
    assert analysis

    # WHEN generating the scout config for the analysis
    result_data = upload_scout_api.generate_config(analysis)

    # THEN the config should contain the vcf2cytosure cgh file path on each sample
    for sample in result_data['samples']:
        assert sample['vcf2cytosure']
