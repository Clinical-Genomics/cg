"""Tests for the file handlers"""
from typing import Optional

from housekeeper.store import models as hk_models

from cg.apps.scout.scout_load_config import ScoutLoadConfig, ScoutMipIndividual
from cg.meta.upload.scout.files import BalsamicFileHandler, MipFileHandler
from cg.meta.upload.scout.hk_tags import BalsamicCaseTags, MipCaseTags


def test_mip_file_handler(hk_version_obj: hk_models.Version):
    # GIVEN a mip file handler

    # WHEN instantiating
    file_handler = MipFileHandler(hk_version_obj=hk_version_obj)

    # THEN assert that the correct case tags was used
    assert isinstance(file_handler.case_tags, MipCaseTags)


def test_balsamic_file_handler(hk_version_obj: hk_models.Version):
    # GIVEN a balsamic file handler

    # WHEN instantiating
    file_handler = BalsamicFileHandler(hk_version_obj=hk_version_obj)

    # THEN assert that the correct case tags was used
    assert isinstance(file_handler.case_tags, BalsamicCaseTags)


def test_include_delivery_report(mip_analysis_hk_version: hk_models.Version):
    # GIVEN a housekeeper version object with a delivery report
    file_obj: hk_models.File
    report: Optional[hk_models.File] = None
    for file_obj in mip_analysis_hk_version.files:
        tag: hk_models.Tag
        tags = {tag.name for tag in file_obj.tags}
        if "delivery-report" in tags:
            report = file_obj
    assert report
    # GIVEN a mip file handler
    file_handler = MipFileHandler(hk_version_obj=mip_analysis_hk_version)

    # GIVEN a scout load case without a delivery report
    load_case = ScoutLoadConfig()
    assert load_case.delivery_report is None

    # WHEN including the delivery report
    file_handler.include_delivery_report(case=load_case)

    # THEN assert that the delivery report was added
    assert load_case.delivery_report == report.full_path


def test_include_alignment_file_individual(
    mip_analysis_hk_version: hk_models.Version, sample_id: str
):
    # GIVEN a housekeeper version object with a cram file
    file_obj: hk_models.File
    alignment_file: Optional[hk_models.File] = None
    for file_obj in mip_analysis_hk_version.files:
        tag: hk_models.Tag
        tags = {tag.name for tag in file_obj.tags}
        if "cram" in tags:
            alignment_file = file_obj
    assert alignment_file
    # GIVEN a mip file handler
    file_handler = MipFileHandler(hk_version_obj=mip_analysis_hk_version)

    # GIVEN a scout load case without a delivery report
    mip_individual = ScoutMipIndividual(sample_id=sample_id)
    assert mip_individual.alignment_path is None

    # WHEN including the delivery report
    file_handler.include_sample_alignment_file(sample=mip_individual)

    # THEN assert that the delivery report was added
    assert mip_individual.alignment_path == alignment_file.full_path
