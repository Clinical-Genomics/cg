from cg.models.dolores.application import Application


def test_instantiate_dolores_application(dolores_application_raw: dict):
    """
    Tests Dolores application model
    """
    # GIVEN a dictionary with the some application data

    # WHEN instantiating a Application object
    dolores_application = Application(**dolores_application_raw)

    # THEN assert that it was successfully created
    assert isinstance(dolores_application, Application)


def test_instantiate_dolores_application_with_required_sample_concentration(
    dolores_application_raw: dict,
):
    """
    Tests Dolores application model when building required sample concentration
    """
    # GIVEN a dictionary with the some application data

    # WHEN instantiating a Application object
    dolores_application = Application(**dolores_application_raw)

    # THEN assert that it the required sample concentration is set
    assert dolores_application.required_sample_concentration == "50 - 250 ng/uL"


def test_instantiate_dolores_application_expected_reads(
    dolores_application_raw: dict,
):
    """
    Tests Dolores application model when setting expected_reads
    """
    # GIVEN a dictionary with the some application data

    # WHEN instantiating a Application object
    dolores_application = Application(**dolores_application_raw)

    # THEN assert that it the expected reads are set
    assert dolores_application.expected_reads == int(
        dolores_application.target_sequence_reads
        * dolores_application.percent_reads_guaranteed
        / 100
    )
