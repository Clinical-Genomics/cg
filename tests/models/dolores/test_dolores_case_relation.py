import datetime

from cg.models.dolores.case_relation import CaseRelation


def test_instantiate_dolores_case_relation(dolores_case_relation_raw: dict):
    """
    Tests Dolores case_relation model
    """
    # GIVEN a dictionary with the some case relation data

    # WHEN instantiating a CaseRelation object
    dolores_case_relation = CaseRelation(**dolores_case_relation_raw)

    # THEN assert that it was successfully created
    assert isinstance(dolores_case_relation, CaseRelation)


def test_instantiate_dolores_case_relation_created_at(dolores_case_relation_raw: dict):
    """
    Tests Dolores case_relation model
    """
    # GIVEN a dictionary with the some case relation date

    # WHEN instantiating a CaseRelation object
    dolores_case_relation = CaseRelation(**dolores_case_relation_raw)

    # THEN assert that created at was set
    assert (
        dolores_case_relation.created_at
        == datetime.datetime.strptime("1999-12-31", "%Y-%m-%d").date()
    )
