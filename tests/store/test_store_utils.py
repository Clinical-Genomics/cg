"""Tests for utils in store"""
from cg.store.models import FamilySample
from cg.store.utils import get_links, get_samples


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
