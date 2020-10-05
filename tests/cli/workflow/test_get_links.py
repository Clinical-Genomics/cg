"""Tests for the cli workflows get links function"""

import click
import pytest

from cg.cli.workflow.get_links import get_links


def test_get_links_case_id(analysis_store):
    """Test to get links for a case id in a populated store with linked samples"""
    # GIVEN a populated store with linked samples
    case_obj = analysis_store.Family.query.first()
    assert case_obj.links

    # WHEN fetching the links for the case
    link_objs = get_links(store=analysis_store, case_id=case_obj.internal_id)

    # THEN assert that the correct links where found
    assert link_objs == case_obj.links


def test_get_links_non_existing_case_id(analysis_store, caplog):
    """Test to get links for a case id in a populated store with linked samples"""
    # GIVEN a populated store with linked samples and a non existing case id
    case_id = "hello"
    case_obj = analysis_store.family(case_id)
    assert not case_obj

    # WHEN fetching the links for the case
    with pytest.raises(click.Abort):
        # THEN assert that it was aborted
        get_links(store=analysis_store, case_id=case_id)
        # THEN assert it communicates that the case_id could not be found
        assert f"could not find case {case_id}" in caplog.text


def test_get_links_case_id_no_links(base_store, helpers, workflow_case_id, caplog):
    """Test to get links for a case id in a populated store where samples are NOT linked"""
    # GIVEN a populated store with unlinked samples
    helpers.add_family(base_store, workflow_case_id)
    helpers.add_sample(base_store, "dna_sample", is_rna=False)

    case_obj = base_store.Family.query.first()
    case_id = case_obj.internal_id
    assert case_obj
    assert not case_obj.links

    # WHEN fetching the links for the case
    with pytest.raises(click.Abort):
        # THEN assert that it was aborted
        get_links(store=base_store, case_id=case_id)
        # THEN assert it communicates that the case_id could not be found
        assert f"Could not find links for case {case_id}" in caplog.text


def test_get_links_sample_id_and_case_id(analysis_store):
    """Test to get links for a sample id in a populated store with linked samples"""
    # GIVEN a populated store with linked samples
    sample_obj = analysis_store.Sample.query.first()
    assert sample_obj
    sample_id = sample_obj.internal_id

    case_obj = analysis_store.Family.query.first()
    assert case_obj
    case_id = case_obj.internal_id

    link_obj = analysis_store.link(family_id=case_id, sample_id=sample_id)
    assert link_obj

    # WHEN fetching the links for the sample in specific case
    link_objs = get_links(store=analysis_store, case_id=case_id, sample_id=sample_id)
    # THEN assert that the correct links where found
    assert link_objs == [link_obj]


def test_get_links_case_id_and_sample_id_no_links(base_store, helpers, workflow_case_id, caplog):
    """Test to get links for a case id in a populated store where samples are NOT linked"""
    # GIVEN a populated store with unlinked samples
    helpers.add_family(base_store, workflow_case_id)
    helpers.add_sample(base_store, "dna_sample", is_rna=False)

    case_obj = base_store.Family.query.first()
    assert case_obj
    case_id = case_obj.internal_id
    assert not case_obj.links

    sample_obj = base_store.Sample.query.first()
    assert sample_obj
    sample_id = sample_obj.internal_id
    assert not sample_obj.links

    # WHEN fetching the links for the case
    with pytest.raises(click.Abort):
        # THEN assert that it was aborted
        get_links(store=base_store, case_id=case_id, sample_id=sample_id)
        # THEN assert it communicates that the case_id could not be found
        assert f"Could not find link for case {case_id} and sample {sample_id}" in caplog.text


def test_get_links_sample_id(analysis_store):
    """Test to get links for a sample id in a populated store with linked samples"""
    # GIVEN a populated store with linked samples
    sample_obj = analysis_store.Sample.query.first()
    assert sample_obj.links

    # WHEN fetching the links for the sample
    link_objs = get_links(store=analysis_store, sample_id=sample_obj.internal_id)
    # THEN assert that the correct links where found
    assert link_objs == sample_obj.links


def test_get_links_non_existing_sample_id(analysis_store, caplog):
    """Test to get links for a sample_id that does not exist"""
    # GIVEN a populated store with linked samples
    non_existing = "hello"
    sample_obj = analysis_store.sample(non_existing)
    assert not sample_obj

    # WHEN fetching the links for the sample
    with pytest.raises(click.Abort):
        # THEN assert that an exception is raised
        get_links(store=analysis_store, sample_id=non_existing)
        # THEN assert it communicates that sample_id did not exist
        assert "Could not find sample" in caplog.text


def test_get_links_sample_id_no_links(base_store, helpers, caplog):
    """Test to get links for a sample in a populated store where samples are NOT linked"""
    # GIVEN a populated store with unlinked samples
    helpers.add_sample(base_store, "dna_sample", is_rna=False)

    sample_obj = base_store.Sample.query.first()
    assert sample_obj
    sample_id = sample_obj.internal_id
    assert not sample_obj.links

    # WHEN fetching the links for the case
    with pytest.raises(click.Abort):
        # THEN assert that it was aborted
        get_links(store=base_store, sample_id=sample_id)
        # THEN assert it communicates that the case_id could not be found
        assert f"Could not find any links" in caplog.text


def test_get_links_no_case_id_no_sample_id(analysis_store, caplog):
    """Test to get links for a case id in a populated store with linked samples"""
    # GIVEN a populated store with linked samples

    # WHEN fetching the links for the case without giving sample_id or case_is
    with pytest.raises(click.Abort):
        # THEN assert that an exception is raised
        get_links(store=analysis_store)
        # THEN assert it communicates that sample_id and/or case_id must be used
        assert "provide case and/or sample" in caplog.text
