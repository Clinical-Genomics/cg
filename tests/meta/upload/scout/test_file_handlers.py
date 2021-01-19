"""Tests for the file handlers"""

from housekeeper.store import models as hk_models

from cg.meta.upload.scout.files import MipFileHandler
from cg.meta.upload.scout.hk_tags import MipCaseTags


def test_mip_file_handler(hk_version_obj: hk_models.Version):
    # GIVEN a mip file handler

    # WHEN instantiating
    file_handler = MipFileHandler(hk_version_obj=hk_version_obj)

    # THEN assert that the correct case tags was used
    assert isinstance(file_handler.case_tags, MipCaseTags)
