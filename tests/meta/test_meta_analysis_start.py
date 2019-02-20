from datetime import datetime

from cg.store import Store
from cg.meta.analysis import AnalysisAPI


def test_start_generates_analysis(analysis_store: Store, analysis_api: AnalysisAPI):
    """Start analysis should create an analysis object"""

    # GIVEN a status db with a family with a priority without analyses
    family = analysis_store.families().first()
    assert not family.analyses
    family.priority = 1

    # WHEN starting an analysis
    analysis_api.start(family)

    # THEN we should have an analysis object
    assert family.analyses
    assert family.analyses[0].is_primary
    assert family.analyses[0].created_at.date() == datetime.now().date()
    assert family.analyses[0].pipeline
    assert family.analyses[0].pipeline_version is None
    assert family.analyses[0].completed_at is None


def test_start_2nd_generates_non_primary_analysis(analysis_store: Store, analysis_api: AnalysisAPI):
    """Second start analysis should create another analysis object"""

    # GIVEN a status db with a family with a priority without analyses
    family = analysis_store.families().first()
    family.analyses.append(analysis_store.add_analysis(pipeline='test_pipeline', primary=True))

    family.priority = 1

    # WHEN starting an analysis
    analysis_api.start(family)

    # THEN we should have an analysis object
    assert len(family.analyses) > 1
    assert family.analyses[0].is_primary
    assert not family.analyses[1].is_primary
