"""This file tests the analyses_to_clean part of the status api"""
from datetime import datetime

from cg.store import Store


def test_analysis_included(analysis_store: Store, helpers):
    """Tests that analyses that are uploaded are returned"""

    # GIVEN an analysis that is uploaded
    timestamp = datetime.now()
    analysis = helpers.add_analysis(
        analysis_store, started_at=timestamp, uploaded_at=timestamp, cleaned_at=None
    )
    sample = helpers.add_sample(analysis_store, delivered_at=timestamp)
    analysis_store.relate_sample(family=analysis.family, sample=sample, status="unknown")

    # WHEN calling the analyses_to_clean
    analyses_to_clean = analysis_store.analyses_to_clean(before=analysis.started_at).all()

    # THEN this analyse should be returned
    assert analysis in analyses_to_clean


def test_analysis_excluded(analysis_store: Store, helpers):
    """Tests that analyses that are completed but lacks delivery report are returned"""

    # GIVEN an analysis that is not uploaded
    timestamp = datetime.now()
    analysis = helpers.add_analysis(
        analysis_store, started_at=timestamp, uploaded_at=None, cleaned_at=None
    )
    sample = helpers.add_sample(analysis_store, delivered_at=timestamp)
    analysis_store.relate_sample(family=analysis.family, sample=sample, status="unknown")

    # WHEN calling the analyses_to_clean
    analyses_to_clean = analysis_store.analyses_to_clean().all()

    # THEN this analyse should be returned
    assert analysis not in analyses_to_clean


def test_pipeline_included(analysis_store: Store, helpers):
    """Tests that analyses that are included depending on pipeline"""

    # GIVEN an analysis that is uploaded and pipeline is specified
    timestamp = datetime.now()
    pipeline = "pipeline"
    analysis = helpers.add_analysis(
        analysis_store,
        pipeline=pipeline,
        started_at=timestamp,
        uploaded_at=timestamp,
        cleaned_at=None,
    )
    sample = helpers.add_sample(analysis_store, delivered_at=timestamp)
    analysis_store.relate_sample(family=analysis.family, sample=sample, status="unknown")

    # WHEN calling the analyses_to_clean specifying the used pipeline
    analyses_to_clean = analysis_store.analyses_to_clean(pipeline=pipeline, before=timestamp).all()

    # THEN this analyse should be returned
    assert analysis in analyses_to_clean


def test_pipeline_excluded(analysis_store: Store, helpers):
    """Tests that analyses are excluded depending on pipeline"""

    # GIVEN an analysis that is uploaded
    timestamp = datetime.now()
    used_pipeline = "pipeline"
    wrong_pipeline = "wrong_pipeline"
    analysis = helpers.add_analysis(
        analysis_store,
        pipeline=used_pipeline,
        started_at=timestamp,
        uploaded_at=timestamp,
        cleaned_at=None,
    )
    sample = helpers.add_sample(analysis_store, delivered_at=timestamp)
    analysis_store.relate_sample(family=analysis.family, sample=sample, status="unknown")

    # WHEN calling the analyses_to_clean specifying another pipeline
    analyses_to_clean = analysis_store.analyses_to_clean(pipeline=wrong_pipeline).all()

    # THEN this analyse should not be returned
    assert analysis not in analyses_to_clean


def test_non_cleaned_included(analysis_store: Store, helpers):
    """Tests that analyses that are included depending on cleaned_at"""

    # GIVEN an analysis that is uploaded but not cleaned
    timestamp = datetime.now()
    analysis = helpers.add_analysis(
        analysis_store, started_at=timestamp, uploaded_at=timestamp, cleaned_at=None
    )
    sample = helpers.add_sample(analysis_store, delivered_at=timestamp)
    analysis_store.relate_sample(family=analysis.family, sample=sample, status="unknown")

    # WHEN calling the analyses_to_clean
    analyses_to_clean = analysis_store.analyses_to_clean(before=timestamp).all()

    # THEN this analyse should be returned
    assert analysis in analyses_to_clean


def test_cleaned_excluded(analysis_store: Store, helpers):
    """Tests that analyses are excluded depending on cleaned_at"""

    # GIVEN an analysis that is cleaned
    timestamp = datetime.now()
    analysis = helpers.add_analysis(
        analysis_store, started_at=timestamp, uploaded_at=timestamp, cleaned_at=timestamp
    )
    sample = helpers.add_sample(analysis_store, delivered_at=timestamp)
    analysis_store.relate_sample(family=analysis.family, sample=sample, status="unknown")

    # WHEN calling the analyses_to_clean
    analyses_to_clean = analysis_store.analyses_to_clean().all()

    # THEN this analyse should not be returned
    assert analysis not in analyses_to_clean
