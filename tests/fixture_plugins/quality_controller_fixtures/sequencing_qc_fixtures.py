import pytest

from cg.store.models import Sample
from cg.constants.priority import Priority
from cg.constants.constants import PrepCategory, Workflow

from tests.fixture_plugins.quality_controller_fixtures.sequencing_qc_check_scenario import (
    SequencingQCCheckScenarios,
)


@pytest.fixture(scope="function")
def sequencing_qc_check_scenarios(store, helpers) -> SequencingQCCheckScenarios:
    return SequencingQCCheckScenarios(store=store, helpers=helpers)


@pytest.fixture(scope="function")
def ready_made_library_sample_pass_sequencing_qc(
    sequencing_qc_check_scenarios: SequencingQCCheckScenarios,
) -> Sample:
    return sequencing_qc_check_scenarios.sample_scenario(
        priority=Priority.standard,
        prep_category=PrepCategory.READY_MADE_LIBRARY,
        pass_sequencing_qc=True,
    )


@pytest.fixture(scope="function")
def ready_made_library_sample_fail_sequencing_qc(
    sequencing_qc_check_scenarios: SequencingQCCheckScenarios,
) -> Sample:
    return sequencing_qc_check_scenarios.sample_scenario(
        priority=Priority.standard,
        prep_category=PrepCategory.READY_MADE_LIBRARY,
        pass_sequencing_qc=False,
    )


@pytest.fixture(scope="function")
def express_sample_pass_sequencing_qc(
    sequencing_qc_check_scenarios: SequencingQCCheckScenarios,
) -> Sample:
    return sequencing_qc_check_scenarios.sample_scenario(
        priority=Priority.express,
        prep_category=PrepCategory.WHOLE_GENOME_SEQUENCING,
        pass_sequencing_qc=True,
    )


@pytest.fixture(scope="function")
def express_sample_fail_sequencing_qc(
    sequencing_qc_check_scenarios: SequencingQCCheckScenarios,
) -> Sample:
    return sequencing_qc_check_scenarios.sample_scenario(
        priority=Priority.express,
        prep_category=PrepCategory.WHOLE_GENOME_SEQUENCING,
        pass_sequencing_qc=False,
    )


@pytest.fixture(scope="function")
def sample_pass_sequencing_qc(
    sequencing_qc_check_scenarios: SequencingQCCheckScenarios,
) -> Sample:
    return sequencing_qc_check_scenarios.sample_scenario(
        priority=Priority.standard,
        prep_category=PrepCategory.WHOLE_GENOME_SEQUENCING,
        pass_sequencing_qc=True,
    )


@pytest.fixture(scope="function")
def sample_fail_sequencing_qc(
    sequencing_qc_check_scenarios: SequencingQCCheckScenarios,
) -> Sample:
    return sequencing_qc_check_scenarios.sample_scenario(
        priority=Priority.standard,
        prep_category=PrepCategory.WHOLE_GENOME_SEQUENCING,
        pass_sequencing_qc=False,
    )


@pytest.fixture(scope="function")
def case_pass_sequencing_qc(
    sequencing_qc_check_scenarios: SequencingQCCheckScenarios,
) -> Sample:
    return sequencing_qc_check_scenarios.case_scenario(
        priority=Priority.standard,
        pass_sequencing_qc=True,
        prep_category=PrepCategory.WHOLE_GENOME_SEQUENCING,
        workflow=Workflow.MIP_DNA,
    )


@pytest.fixture(scope="function")
def case_fail_sequencing_qc(
    sequencing_qc_check_scenarios: SequencingQCCheckScenarios,
) -> Sample:
    return sequencing_qc_check_scenarios.case_scenario(
        priority=Priority.standard,
        pass_sequencing_qc=False,
        prep_category=PrepCategory.WHOLE_GENOME_SEQUENCING,
        workflow=Workflow.MIP_DNA,
    )


@pytest.fixture(scope="function")
def express_case_pass_sequencing_qc(
    sequencing_qc_check_scenarios: SequencingQCCheckScenarios,
) -> Sample:
    return sequencing_qc_check_scenarios.case_scenario(
        priority=Priority.express,
        pass_sequencing_qc=True,
        prep_category=PrepCategory.WHOLE_GENOME_SEQUENCING,
        workflow=Workflow.MIP_DNA,
    )


@pytest.fixture(scope="function")
def express_case_fail_sequencing_qc(
    sequencing_qc_check_scenarios: SequencingQCCheckScenarios,
) -> Sample:
    return sequencing_qc_check_scenarios.case_scenario(
        priority=Priority.express,
        pass_sequencing_qc=False,
        prep_category=PrepCategory.WHOLE_GENOME_SEQUENCING,
        workflow=Workflow.MIP_DNA,
    )

@pytest.fixture(scope="function")
def any_sample_in_case_has_reads(
    sequencing_qc_check_scenarios: SequencingQCCheckScenarios,
) -> Sample:
    return sequencing_qc_check_scenarios.case_scenario(
        priority=Priority.standard,
        pass_sequencing_qc=True,
        prep_category=PrepCategory.WHOLE_GENOME_SEQUENCING,
        workflow=Workflow.MIP_DNA,
    )
    
@pytest.fixture(scope="function")
def any_sample_in_case_no_reads(
    sequencing_qc_check_scenarios: SequencingQCCheckScenarios,
) -> Sample:
    return sequencing_qc_check_scenarios.case_scenario(
        priority=Priority.standard,
        pass_sequencing_qc=False,
        prep_category=PrepCategory.WHOLE_GENOME_SEQUENCING,
        workflow=Workflow.MIP_DNA,
    )