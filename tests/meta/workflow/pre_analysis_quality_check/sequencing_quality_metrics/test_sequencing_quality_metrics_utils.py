import pytest
from cg.constants.constants import PrepCategory, Workflow
from cg.constants.priority import Priority
from cg.store.models import Case, Sample
from cg.meta.workflow.pre_analysis_quality_check.sequencing_quality_metrics.utils import (
    is_sample_ready_made_library,
    case_has_express_priority,
    sample_has_express_priority,
    case_has_lower_priority_than_express,
    ready_made_library_sample_has_enough_reads,
    sample_has_enough_reads,
    get_sequencing_qc_of_case,
    get_express_reads_threshold_for_sample,
    express_sample_has_enough_reads,
    get_express_sequencing_qc_of_case,
    any_sample_in_case_has_reads,
)
from cg.store.store import Store
from tests.conftest import StoreHelpers
from tests.meta.workflow.pre_analysis_quality_check.conftest import ScenariosGenerator


@pytest.mark.parametrize(
    "prep_category, expected_result",
    [
        (PrepCategory.READY_MADE_LIBRARY, True),
        (PrepCategory.WHOLE_GENOME_SEQUENCING, False),
    ],
    ids=["ready_made_library", "whole_genome_sequencing"],
)
def test_is_sample_ready_made_library(
    prep_category: PrepCategory, expected_result: bool, base_store: Store, helpers
):
    """
    Test the is_sample_ready_made_library function.

    This test verifies if the sample is ready-made library based on its prep category.

    Arguments:
        prep_category (PrepCategory): The prep category of the sample.
        expected_result (bool): The expected result of the function.
        base_store (Store): The base store fixture.
        helpers: The helpers fixture.
    """
    scenarios_generator: ScenariosGenerator = ScenariosGenerator(store=base_store, helpers=helpers)
    sample: Sample = scenarios_generator.sample_scenario(
        priority=Priority.standard, prep_category=prep_category, pass_reads=True
    )

    assert is_sample_ready_made_library(sample) == expected_result


@pytest.mark.parametrize(
    "priority, expected_result",
    [
        (Priority.express, True),
        (Priority.standard, False),
    ],
    ids=["express_priority", "standard_priority"],
)
def test_case_has_express_priority(
    priority: Priority, expected_result: bool, base_store: Store, helpers
):
    """
    Test the case_has_express_priority function.

    This test verifies if the case has express priority.

    Arguments:
        priority (Priority): The priority of the case.
        expected_result (bool): The expected result of the function.
        base_store (Store): The base store fixture.
        helpers: The helpers fixture.
    """
    scenarios_generator: ScenariosGenerator = ScenariosGenerator(store=base_store, helpers=helpers)
    case: Case = scenarios_generator.case_scenario(
        priority=priority,
        pass_reads=True,
        prep_category=PrepCategory.READY_MADE_LIBRARY,
        workflow=Workflow.MIP_DNA,
    )
    assert case_has_express_priority(case) == expected_result


@pytest.mark.parametrize(
    "priority, expected_result",
    [
        (Priority.express, True),
        (Priority.standard, False),
    ],
    ids=["express_priority", "standard_priority"],
)
def test_sample_has_express_priority(
    priority: Priority, expected_result: bool, base_store: Store, helpers
):
    """
    Test the sample_has_express_priority function.

    This test verifies if the sample has express priority.

    Arguments:
        priority (Priority): The priority of the sample.
        expected_result (bool): The expected result of the function.
        base_store (Store): The base store fixture.
        helpers: The helpers fixture.
    """
    scenarios_generator: ScenariosGenerator = ScenariosGenerator(store=base_store, helpers=helpers)
    sample: Sample = scenarios_generator.sample_scenario(
        priority=priority, prep_category=PrepCategory.READY_MADE_LIBRARY, pass_reads=True
    )
    assert sample_has_express_priority(sample) == expected_result


@pytest.mark.parametrize(
    "priority, expected_result",
    [
        (Priority.express, False),
        (Priority.standard, True),
    ],
    ids=["express_priority", "standard_priority"],
)
def test_case_has_lower_priority_than_express(
    priority: Priority, expected_result: bool, base_store: Store, helpers
):
    """
    Test the case_has_lower_priority_than_express function.

    This test verifies if the case has lower priority than express. It checks if the case has lower priority than express.
    It checks if the case has lower priority than express.
    """
    scenarios_generator: ScenariosGenerator = ScenariosGenerator(store=base_store, helpers=helpers)
    case: Case = scenarios_generator.case_scenario(
        priority=priority,
        pass_reads=True,
        prep_category=PrepCategory.WHOLE_EXOME_SEQUENCING,
        workflow=Workflow.MIP_DNA,
    )
    assert case_has_lower_priority_than_express(case) == expected_result


@pytest.mark.parametrize(
    "pass_reads, expected_result",
    [
        (True, True),
        (False, False),
    ],
    ids=["pass_reads", "no_reads"],
)
def test_ready_made_library_sample_has_enough_reads(
    pass_reads: bool, expected_result: bool, base_store: Store, helpers
):
    """
    Test the ready_made_library_sample_has_enough_reads function.

    This test verifies if the ready-made library sample has enough reads. It checks if the sample is a ready made
    library and if it has enough reads if so is the case.
    """
    scenarios_generator: ScenariosGenerator = ScenariosGenerator(store=base_store, helpers=helpers)
    sample: Sample = scenarios_generator.ready_made_library_sample_scenario(
        priority=Priority.standard,
        pass_reads=pass_reads,
    )
    assert ready_made_library_sample_has_enough_reads(sample) == expected_result


@pytest.mark.parametrize(
    "pass_reads, expected_result",
    [
        (True, True),
        (False, False),
    ],
    ids=["pass_reads", "no_reads"],
)
def test_sample_has_enough_reads(
    pass_reads: bool, expected_result: bool, base_store: Store, helpers
):
    """
    Test the sample_has_enough_reads function.

    This test verifies if the sample has enough reads. It checks if the sample has enough reads or not.
    """
    scenarios_generator: ScenariosGenerator = ScenariosGenerator(store=base_store, helpers=helpers)
    sample: Sample = scenarios_generator.sample_scenario(
        priority=Priority.standard,
        prep_category=PrepCategory.WHOLE_EXOME_SEQUENCING,
        pass_reads=pass_reads,
    )
    assert sample_has_enough_reads(sample) == expected_result


@pytest.mark.parametrize(
    "pass_reads, priority, expected_result",
    [
        (True, Priority.standard, True),
        (False, Priority.standard, False),
    ],
    ids=["standard_priority", "standard_priority_no_reads"],
)
def test_get_sequencing_qc_of_case(pass_reads, priority, expected_result, base_store, helpers):
    """
    Test the get_sequencing_qc_of_case function.

    This test verifies the sequencing quality check of the case. It checks if the case has enough
    reads and if it has lower priority than express.

    """
    scenarios_generator: ScenariosGenerator = ScenariosGenerator(store=base_store, helpers=helpers)
    case: Case = scenarios_generator.case_scenario(
        priority=priority,
        pass_reads=pass_reads,
        prep_category=PrepCategory.WHOLE_EXOME_SEQUENCING,
        workflow=Workflow.MIP_DNA,
    )
    assert get_sequencing_qc_of_case(case) == expected_result


@pytest.mark.parametrize(
    "pass_reads, priority, expected_result",
    [
        (True, Priority.express, True),
        (False, Priority.express, False),
    ],
    ids=["express_priority", "express_priority_no_reads"],
)
def test_express_sample_has_enough_reads(
    pass_reads, priority, expected_result, base_store, helpers
):
    """
    Test the express_sample_has_enough_reads function.

    This test verifies the sequencing quality check of the express sample. It checks if the express sample has enough
    reads.

    """
    scenarios_generator: ScenariosGenerator = ScenariosGenerator(store=base_store, helpers=helpers)
    sample: Sample = scenarios_generator.sample_scenario(
        priority=priority,
        prep_category=PrepCategory.WHOLE_EXOME_SEQUENCING,
        pass_reads=pass_reads,
    )
    assert express_sample_has_enough_reads(sample) == expected_result


def test_get_express_reads_threshold_for_sample(base_store, helpers):
    """
    Test the get_express_reads_threshold_for_sample function.

    This test verifies the express reads threshold is correctly calculated for a sample.
    """
    # GIVEN a sample with a target reads value
    scenarios_generator: ScenariosGenerator = ScenariosGenerator(store=base_store, helpers=helpers)
    sample: Sample = scenarios_generator.sample_scenario(
        priority=Priority.express,
        prep_category=PrepCategory.WHOLE_EXOME_SEQUENCING,
        pass_reads=True,
    )
    sample.application_version.application.target_reads = 10
    expected_express_reads_threshold = 5
    # WHEN getting the express reads threshold for the sample
    express_reads_threshold: int = get_express_reads_threshold_for_sample(sample)
    # THEN the express reads threshold should be half of the target reads
    assert express_reads_threshold == expected_express_reads_threshold == 5


@pytest.mark.parametrize(
    "pass_reads, priority, expected_result",
    [
        (True, Priority.express, True),
        (False, Priority.express, False),
    ],
    ids=["express_priority", "express_priority_no_reads"],
)
def test_get_express_sequencing_qc_of_case(
    pass_reads: bool, priority: Priority, expected_result: bool, base_store, helpers
):
    """
    Test the get_express_sequencing_qc_of_case function.

    This test verifies the express sequencing quality check of the case. It checks if the case has enough
    reads and if it has express priority.
    """

    # GIVEN a case with express priority and a sample
    scenarios_generator: ScenariosGenerator = ScenariosGenerator(store=base_store, helpers=helpers)
    case: Case = scenarios_generator.case_scenario(
        priority=priority,
        pass_reads=pass_reads,
        prep_category=PrepCategory.WHOLE_EXOME_SEQUENCING,
        workflow=Workflow.MIP_DNA,
    )
    # WHEN getting the express sequencing quality check of the case
    express_sequencing_qc_of_case: bool = get_express_sequencing_qc_of_case(case)
    # THEN the express sequencing quality check of the case should be as expected
    assert express_sequencing_qc_of_case == expected_result


@pytest.mark.parametrize(
    "pass_reads, expected_result",
    [
        (True, True),
        (False, False),
    ],
    ids=["on_sample_with_reads", "no_sample_with_reads"],
)
def test_any_sample_in_case_has_reads(
    pass_reads: bool, expected_result: bool, base_store: Store, helpers: StoreHelpers
):
    """
    Test the any_sample_in_case_has_reads function.

    This test verifies if any sample in the case has reads.
    """
    # GIVEN a case with a sample with or without reads
    scenarios_generator: ScenariosGenerator = ScenariosGenerator(store=base_store, helpers=helpers)
    case: Case = scenarios_generator.case_scenario(
        priority=Priority.standard,
        pass_reads=pass_reads,
        prep_category=PrepCategory.WHOLE_EXOME_SEQUENCING,
        workflow=Workflow.MIP_DNA,
    )
    # GIVEN that another sample on the case has no reads
    another_sample: Sample = scenarios_generator.add_sample(
        prep_category=PrepCategory.WHOLE_EXOME_SEQUENCING, pass_reads=False
    )
    helpers.add_relationship(store=base_store, sample=another_sample, case=case)
    # WHEN checking if any sample in the case has reads
    any_sample_in_case_has_reads_result: bool = any_sample_in_case_has_reads(case)
    # THEN the result should be as expected
    assert any_sample_in_case_has_reads_result == expected_result
