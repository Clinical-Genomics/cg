from cg.constants.constants import Workflow
from cg.store.models import Analysis
from cg.store.store import Store


def test_creating_an_analysis_model_with_a_trailblazer_id(store: Store):
    # GIVEN a trailblazer id
    trailblazer_id = 12345

    # WHEN an analysis is added
    analysis: Analysis = store.add_analysis(
        workflow=Workflow.BALSAMIC, trailblazer_id=trailblazer_id
    )

    # THEN a new analysis is returned with the trailblazer id set
    assert isinstance(analysis, Analysis)
    assert analysis.trailblazer_id == trailblazer_id
