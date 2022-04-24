from cg.constants.subject import Gender
from cg.models.dolores.subject import Subject


def test_instantiate_dolores_subject(dolores_subject_raw: dict):
    """
    Tests Dolores subject model
    """
    # GIVEN a dictionary with the some subject data

    # WHEN instantiating a Subject object
    dolores_subjects = Subject(**dolores_subject_raw)

    # THEN assert that it was successfully created
    assert isinstance(dolores_subjects, Subject)


def test_instantiate_dolores_subjects_with_gender(dolores_subject_raw: dict):
    """
    Tests Dolores subject model with gender
    """
    # GIVEN a dictionary with the some subject data including gender
    dolores_subject_raw.update({"gender": Gender.MALE})

    # WHEN instantiating a Subject object
    dolores_subjects = Subject(**dolores_subject_raw)

    # THEN assert that it was successfully created
    assert dolores_subjects.gender == Gender.MALE
