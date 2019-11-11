"""Tests for the scout upload API"""

from pathlib import Path

import yaml
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


def test_generate_config_adds_vcf2cytosure(analysis: Store.Analysis, upload_scout_api:
                                           UploadScoutAPI):
    # GIVEN a status db and hk with an analysis
    assert analysis

    # WHEN generating the scout config for the analysis
    result_data = upload_scout_api.generate_config(analysis)

    # THEN the config should contain the vcf2cytosure cgh file path on each sample
    for sample in result_data['samples']:
        assert sample['vcf2cytosure']


def _file_exists_on_disk(file_path: Path):
    """Returns if the file exists on disk"""
    return file_path.exists()


def _file_is_yaml(file_path):
    """Returns if the file successfully was loaded as yaml"""

    data = yaml.load(open(file_path, 'r', encoding='utf-8'), Loader=yaml.FullLoader)
    return data is not None


def test_save_config_creates_file(upload_scout_api: UploadScoutAPI, tmpdir):
    """"Tests that save config creates a file"""

    # GIVEN a scout_config dict and a path to save it on
    scout_config = {'dummy': 'data'}
    file_path = Path(tmpdir / 'test')

    # WHEN calling method to save config
    result_data = upload_scout_api.save_config_file(upload_config=scout_config,
                                                    file_path=file_path)

    # THEN the config should exist on disk
    assert _file_exists_on_disk(file_path)


def test_save_config_creates_yaml(upload_scout_api: UploadScoutAPI, tmp_path):
    """Tests that the file created by save_config_file create a yaml """

    # GIVEN a scout_config dict and a path to save it on
    scout_config = {'dummy': 'data'}
    file_path = tmp_path

    # WHEN calling method to save config
    result_data = upload_scout_api.save_config_file(upload_config=scout_config,
                                                    file_path=file_path)

    # THEN the should be of yaml type
    assert _file_is_yaml(file_path)
