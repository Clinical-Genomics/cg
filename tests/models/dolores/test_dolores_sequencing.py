from cg.models.dolores.sample import Sequencing


def test_instantiate_dolores_sequencing(dolores_sequencing_raw: dict):
    """
    Tests Dolores sequencing model
    """
    # GIVEN a dictionary with the some sequencing data

    # WHEN instantiating a Sequencing object
    dolores_sequencings = Sequencing(**dolores_sequencing_raw)

    # THEN assert that it was successfully created
    assert isinstance(dolores_sequencings, Sequencing)
