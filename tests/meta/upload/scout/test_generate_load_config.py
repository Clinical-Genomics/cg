"""Test the methods that generate a scout load config"""


from cg.apps.scout.scout_load_config import MipLoadConfig, ScoutLoadConfig
from cg.meta.upload.scout.files import MipFileHandler
from cg.meta.upload.scout.scoutapi import UploadScoutAPI
from cg.store import models


def test_generate_mip_config(analysis_obj: models.Analysis, mip_file_handler: MipFileHandler):
    # GIVEN an cg analysis object
    # GIVEN a mip load config object
    load_config = MipLoadConfig()
    # GIVEN a file handler with some housekeeper version data

    # WHEN adding the mandatory information
    config = UploadScoutAPI.add_mandatory_info_to_load_config(
        analysis_obj=analysis_obj, load_config=load_config, file_handler=mip_file_handler
    )

    # THEN assert it was instantiated in the correct way
    assert isinstance(config, ScoutLoadConfig)
