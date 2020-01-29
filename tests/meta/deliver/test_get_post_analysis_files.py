"""Tests for mip_dna delivery API"""

import pytest

from cg.apps.hk import HousekeeperAPI
from cg.apps.lims import LimsAPI
from cg.meta.deliver.mip_dna import DeliverAPI
from cg.store import Store

tags = ["bam", "bam-index"]
version = None


def test_get_post_analysis_files(analysis_family, mip_dna_deliver_api):

    ## GIVEN a family and tags
    family = analysis_family["name"]

    ## WHEN no version
    files = mip_dna_deliver_api.get_post_analysis_files(family, version, tags)

    ## THEN housekeeper files should be returned
    assert files


def test_get_post_analysis_files_version(analysis_family, mip_dna_deliver_api):

    ## GIVEN a family and tags
    family = analysis_family["name"]

    ## WHEN version
    version = "a_date"

    files_version = mip_dna_deliver_api.get_post_analysis_files(family, version, tags)

    ## THEN housekeeper files should be returned
    assert files_version
