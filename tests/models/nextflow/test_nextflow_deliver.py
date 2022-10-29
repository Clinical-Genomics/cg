import pytest
from cg.models.nextflow.deliverable import NextflowDeliverable
import pydantic


def test_instantiate_nextflow_deliverables(
    nextflow_deliverables: dict,
):
    """
    Tests nextflow delivery object
    """
    # GIVEN a sample with fastq files and strandedness

    # WHEN instantiating a deliverables object
    nextflow_deliverables_object = NextflowDeliverable(deliverables=nextflow_deliverables)

    # THEN assert that it was successfully created
    assert isinstance(nextflow_deliverables_object, NextflowDeliverable)


def test_instantiate_nextflow_deliverables_with_empty_entry(
    nextflow_deliverables_with_empty_entry: dict,
):
    """
    Tests nextflow delivery object with empty entry
    """
    # WHEN instantiating a deliverables object with an empty entry THEN assert that it was successfully created
    with pytest.raises(pydantic.ValidationError):
        NextflowDeliverable(deliverables=nextflow_deliverables_with_empty_entry)


def test_instantiate_nextflow_deliverables_with_faulty_entry(
    nextflow_deliverables_with_faulty_entry: dict,
):
    """
    Tests nextflow delivery object with empty entry
    """
    # WHEN instantiating a deliverables object with an empty entry THEN assert that it was successfully created
    with pytest.raises(pydantic.ValidationError):
        NextflowDeliverable(deliverables=nextflow_deliverables_with_faulty_entry)
