"""Tests for utils in store"""

import logging

from cg.store.models import FamilySample
from cg.store.utils import case_exists, get_links, get_samples


def test_case_exists_when_missing(case_id, caplog):
    """Test function when a case object is missing """
    caplog.set_level(logging.DEBUG)
    # GIVEN a case_id
    # WHEN case_obj is None
    was_found = case_exists(None, case_id)
    # THEN case_exists should return None
    assert was_found is None
    # THEN communicate case_id is missing
    assert f"{case_id}: case not found" in caplog.text


def test_case_exists_when_present(family_obj, case_id):
    """Test function when a case object is found """
    # GIVEN a case_id
    # WHEN case_obj is True
    was_found = case_exists(family_obj, case_id)
    # THEN case_exists should return True
    assert was_found


def test_get_samples(analysis_obj):
    """Test function to get all samples from a analysis object"""
    # GIVEN an analysis object
    # WHEN fetching all samples
    samples = get_samples(analysis_obj)
    # THEN assert the samples are FamilySamples
    for sample in samples:
        assert isinstance(sample, FamilySample)


def test_link(family_obj):
    """Test function to get all samples from a family"""
    # GIVEN an family object
    # WHEN fetching all links
    link_objs = get_links(family_obj)
    # THEN assert the link objs are samples
    for link_obj in link_objs:
        assert isinstance(link_obj, FamilySample)
