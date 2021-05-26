"""Tests the findbusinessdata part of the cg.store.api"""
from datetime import datetime


def test_find_analysis_via_date(sample_store, helpers):
    # GIVEN a case with an analysis with a startdate in the database
    analysis = helpers.add_analysis(store=sample_store, started_at=datetime.now())
    assert analysis.started_at

    # WHEN getting analysis via case_id and start date
    db_analysis = sample_store.analysis(analysis.family, analysis.started_at)

    # THEN the analysis should have been retrieved
    assert db_analysis == analysis
