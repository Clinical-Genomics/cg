from cg.constants.subject import Gender
from cg.models.dolores.subject import Subject, SubjectHuman


def test_instantiate_dolores_subject(dolores_subject_raw: dict):
    """
    Tests Dolores subject model
    """
    # GIVEN a dictionary with the some subject data

    # WHEN instantiating a Subject object
    dolores_subject = Subject(**dolores_subject_raw)

    # THEN assert that it was successfully created
    assert isinstance(dolores_subject, Subject)


def test_instantiate_dolores_subject_human(dolores_subject_raw: dict):
    """
    Tests Dolores subject human model
    """
    # GIVEN a dictionary with the some subject data

    # WHEN instantiating a Subject object
    dolores_subject = SubjectHuman(**dolores_subject_raw)

    # THEN assert that it was successfully created
    assert isinstance(dolores_subject, SubjectHuman)


def test_instantiate_dolores_subject_human_with_gender(dolores_subject_raw: dict):
    """
    Tests Dolores subject human model with gender
    """
    # GIVEN a dictionary with the some subject data including gender
    dolores_subject_raw.update({"gender": Gender.MALE})

    # WHEN instantiating a Subject object
    dolores_subject = SubjectHuman(**dolores_subject_raw)

    # THEN assert that it was successfully created
    assert dolores_subject.gender == Gender.MALE
