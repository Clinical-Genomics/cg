"""Tests for cg.cli.store._add_new_complete_analysis_record"""
from datetime import datetime

import pytest
from cg.cli.store import _add_new_complete_analysis_record
from cg.exc import AnalysisDuplicationError
from cg.store import Store


def test_add_new_complete_analysis_record(analysis_store: Store, hk_version_obj):

    # GIVEN A family has samples with data_analysis on them
    pipeline = 'test-pipeline'
    family_with_samples = analysis_store.families().first()
    family_with_samples.links[0].sample.data_analysis = pipeline
    dummy_bundle_data = {'pipeline_version': 'dummy_version'}
    hk_version_obj.created_at = datetime.now()

    # WHEN calling add_new_complete_analysis_record
    new_analysis = _add_new_complete_analysis_record(dummy_bundle_data, family_with_samples,
                                                     analysis_store, hk_version_obj)

    # THEN it should put the pipeline in analysis record
    assert new_analysis['pipeline'] == pipeline


def test_duplicate_add_new_complete_analysis_record_raises(analysis_store: Store, hk_version_obj):

    # GIVEN A family has samples with data_analysis on them
    pipeline = 'test-pipeline'
    family_with_samples = analysis_store.families().first()
    family_with_samples.links[0].sample.data_analysis = pipeline
    dummy_bundle_data = {'pipeline_version': 'dummy_version'}
    hk_version_obj.created_at = datetime.now()
    _add_new_complete_analysis_record(dummy_bundle_data, family_with_samples,
                                      analysis_store, hk_version_obj)

    # WHEN calling add_new_complete_analysis_record
    # THEN it should throw an AnalysisDuplicationError
    with pytest.raises(AnalysisDuplicationError):
        _add_new_complete_analysis_record(dummy_bundle_data, family_with_samples,
                                          analysis_store, hk_version_obj)
