from cg.models.dolores.case import Case


def test_instantiate_dolores_case(dolores_case_raw: dict):
    """
    Tests Dolores case model
    """
    # GIVEN a dictionary with the some case relation data

    # WHEN instantiating a CaseRelation object
    dolores_case = Case(**dolores_case_raw)

    # THEN assert that it was successfully created
    assert isinstance(dolores_case, Case)
