from cg.models.dolores.analysis import Analysis


def test_instantiate_dolores_analysis(dolores_analysis_raw: dict):
    """
    Tests Dolores analysis model
    """
    # GIVEN a dictionary with the some analysis data

    # WHEN instantiating a Analysis object
    dolores_analysis = Analysis(**dolores_analysis_raw)

    # THEN assert that it was successfully created
    assert isinstance(dolores_analysis, Analysis)
