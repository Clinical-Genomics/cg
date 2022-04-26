from datetime import datetime

from cg.constants import Priority
from cg.models.dolores.sample import Sample, ExperimentDesign, SampleCancer, SampleRareDisease


def test_instantiate_dolores_sample(dolores_sample_raw: dict):
    """
    Tests Dolores sample model
    """
    # GIVEN a dictionary with the some sample data

    # WHEN instantiating a Sample object
    dolores_sample = Sample(**dolores_sample_raw)

    # THEN assert that it was successfully created
    assert isinstance(dolores_sample, Sample)


def test_instantiate_dolores_sample_with_created_at(
    datestamp_now: datetime, dolores_sample_raw: dict
):
    """
    Tests Dolores sample model with "created_at"
    """
    # GIVEN a dictionary with the some sample data including created_at
    dolores_sample_raw.update({"created_at": datestamp_now})

    # WHEN instantiating a Sample object
    dolores_sample = Sample(**dolores_sample_raw)

    # THEN assert that it should return the current time
    assert dolores_sample.created_at == datestamp_now


def test_instantiate_dolores_sample_with_priority_str(dolores_sample_raw: dict):
    """
    Tests Dolores sample model with "priority" in str format
    """
    # GIVEN a dictionary with the some sample data including "priority" in str format
    assert isinstance(dolores_sample_raw["priority"], str)

    # WHEN instantiating a Sample object
    dolores_sample = Sample(**dolores_sample_raw)

    # THEN assert that it should return the integer value of the priority
    assert dolores_sample.priority == Priority.standard


def test_instantiate_dolores_sample_with_priority_int(dolores_sample_raw: dict):
    """
    Tests Dolores sample model with "priority" in int format
    """
    # GIVEN a dictionary with the some sample data including "priority" in int format
    dolores_sample_raw.update({"priority": Priority.standard})
    assert isinstance(dolores_sample_raw["priority"], int)

    # WHEN instantiating a Sample object
    dolores_sample = Sample(**dolores_sample_raw)

    # THEN assert that it should return the integer value of the priority
    assert dolores_sample.priority == Priority.standard


def test_instantiate_dolores_sample_total_nr_sequencing_reads_when_no_sequencing(
    dolores_sample_raw: dict,
):
    """
    Tests Dolores sample model when setting total_nr_sequencing_reads when no sequencing has been performed
    """
    # GIVEN a dictionary with the some sample data with no sequencing data
    dolores_sample_raw.pop("sequencing", None)

    # WHEN instantiating a Sample object
    dolores_sample = Sample(**dolores_sample_raw)

    # THEN assert that it should return the integer value of the total_nr_sequencing_reads
    assert dolores_sample.total_nr_sequencing_reads == 0


def test_instantiate_dolores_sample_total_nr_sequencing_reads(
    dolores_sample_raw: dict, nr_of_sequencing_reads: int, nr_of_sequencing_reads_top_up: int
):
    """
    Tests Dolores sample model when setting total_nr_sequencing_reads
    """
    # GIVEN a dictionary with the some sample data including sequencing data

    # WHEN instantiating a Sample object
    dolores_sample = Sample(**dolores_sample_raw)

    # THEN assert that it should return the integer value of the total_nr_sequencing_reads
    assert (
        dolores_sample.total_nr_sequencing_reads
        == nr_of_sequencing_reads + nr_of_sequencing_reads_top_up
    )


def test_instantiate_dolores_experiment_design(dolores_experiment_design_raw: dict):
    """
    Tests Dolores experiment_design model
    """
    # GIVEN a dictionary with the some sample experiment design data

    # WHEN instantiating a ExperimentDesign object
    dolores_experiment_design = ExperimentDesign(**dolores_experiment_design_raw)

    # THEN assert that it was successfully created
    assert isinstance(dolores_experiment_design, ExperimentDesign)


def test_instantiate_dolores_sample_cancer(dolores_sample_raw: dict):
    """
    Tests Dolores sample_cancer model
    """
    # GIVEN a dictionary with the some sample sample cancer data
    dolores_sample_raw.update({"is_tumour": "True"})

    # WHEN instantiating a SampleCancer object
    dolores_sample_cancer = SampleCancer(**dolores_sample_raw)

    # THEN assert that it was successfully created
    assert isinstance(dolores_sample_cancer, SampleCancer)

    # THEN assert that is_tumour is set
    assert dolores_sample_cancer.is_tumour is True


def test_instantiate_dolores_sample_rare_disease(dolores_sample_raw: dict, loqusdb_id: str):
    """
    Tests Dolores sample_rare_disease model
    """
    # GIVEN a dictionary with the some sample sample rare_disease data
    dolores_sample_raw.update({"loqusdb_id": loqusdb_id})

    # WHEN instantiating a SampleRareDisease object
    dolores_sample_rare_disease = SampleRareDisease(**dolores_sample_raw)

    # THEN assert that it was successfully created
    assert isinstance(dolores_sample_rare_disease, SampleRareDisease)

    # THEN assert that loqusdb_id is set
    assert dolores_sample_rare_disease.loqusdb_id == loqusdb_id
