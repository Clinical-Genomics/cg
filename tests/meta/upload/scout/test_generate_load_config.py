"""Test the methods that generate a scout load config"""


from cg.apps.scout.scout_load_config import ScoutLoadConfig
from cg.meta.upload.scout.scoutapi import UploadScoutAPI
from cg.store.models import Analysis


def test_generate_config(analysis_obj: Analysis):
    # GIVEN an cg analysis object

    # WHEN generating a scout load config
    config: ScoutLoadConfig = UploadScoutAPI.get_config_case(analysis_obj)

    # THEN assert it was instantiated in the correct way
    assert isinstance(config, ScoutLoadConfig)
