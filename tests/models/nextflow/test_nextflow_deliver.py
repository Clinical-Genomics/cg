from typing import Dict, Optional

from pydantic.v1 import ValidationError as PydanticValidationError
import pytest

from cg.models.nextflow.deliverables import NextflowDeliverables


def test_instantiate_nextflow_deliverables(
    nextflow_deliverables: Dict[str, str],
):
    """
    Tests nextflow delivery object.
    """
    # GIVEN a sample with fastq files and strandedness

    # WHEN instantiating a deliverables object
    nextflow_deliverables_object: NextflowDeliverables = NextflowDeliverables(
        deliverables=nextflow_deliverables
    )

    # THEN assert that it was successfully created
    assert isinstance(nextflow_deliverables_object, NextflowDeliverables)


def test_instantiate_nextflow_deliverables_with_empty_entry(
    nextflow_deliverables_with_empty_entry: Dict[str, Optional[str]],
):
    """
    Tests nextflow delivery object with empty entry.
    """
    # WHEN instantiating a deliverables object with an empty entry THEN assert that it was successfully created
    with pytest.raises(PydanticValidationError):
        NextflowDeliverables(deliverables=nextflow_deliverables_with_empty_entry)


def test_instantiate_nextflow_deliverables_with_faulty_entry(
    nextflow_deliverables_with_faulty_entry: Dict[str, str],
):
    """
    Tests nextflow delivery object with empty entry.
    """
    # WHEN instantiating a deliverables object with an empty entry THEN assert that it was successfully created
    with pytest.raises(PydanticValidationError):
        NextflowDeliverables(deliverables=nextflow_deliverables_with_faulty_entry)
