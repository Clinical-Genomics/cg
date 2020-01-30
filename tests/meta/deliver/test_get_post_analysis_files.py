"""Tests for mip_dna delivery API"""

import pytest

from cg.apps.hk import HousekeeperAPI
from cg.apps.lims import LimsAPI
from cg.meta.deliver import DeliverAPI
from cg.store import Store


def test_get_post_analysis_files(analysis_family, deliver_api):

    ## GIVEN a family and tags
    family = analysis_family["name"]
    tags = ["bam", "bam-index"]

    ## WHEN no version
    version = None
    files = deliver_api.get_post_analysis_files(family, version, tags)

    ## THEN housekeeper files should be returned
    assert files


def test_get_post_analysis_files_version(analysis_family, deliver_api):

    ## GIVEN a family and tags
    family = analysis_family["name"]
    tags = ["bam", "bam-index"]

    ## WHEN version
    version = "a_date"

    files_version = deliver_api.get_post_analysis_files(family, version, tags)

    ## THEN housekeeper files should be returned
    assert files_version


def test_get_post_analysis_family_files(analysis_family, deliver_api):

    ## GIVEN
    family = analysis_family["name"]
    family_tags = ["gbcf"]
    tags = ["bam", "bam-index"]

    ## WHEN
    version = None
    family_files = deliver_api.get_post_analysis_family_files(
        family, family_tags, version, tags
    )

    assert family_files
