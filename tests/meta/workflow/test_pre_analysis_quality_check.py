import pytest

from cg.constants import Priority
from cg.constants.constants import Pipeline, PrepCategory
from cg.meta.workflow.analysis import AnalysisAPI
from cg.meta.workflow.balsamic import BalsamicAnalysisAPI
from cg.meta.workflow.balsamic_qc import BalsamicQCAnalysisAPI
from cg.meta.workflow.balsamic_umi import BalsamicUmiAnalysisAPI
from cg.meta.workflow.microsalt import MicrosaltAnalysisAPI
from cg.meta.workflow.mip_dna import MipDNAAnalysisAPI
from cg.meta.workflow.mip_rna import MipRNAAnalysisAPI
from cg.meta.workflow.pre_analysis_quality_check import (
    BalsamicPreAnalysisQc,
    FastqPreAnalysisQc,
    MicrobialPreAnalysisQc,
    MIPPreAnalysisQc,
    PreAnalysisQualityCheck,
    RareDiseasePreAnalysisQc,
    RnafusionPreAnalysisQc,
    TaxProfilerPreAnalysisQc,
    get_pre_analysis_quality_check_for_workflow,
)
from cg.meta.workflow.raredisease import RarediseaseAnalysisAPI
from cg.meta.workflow.rnafusion import RnafusionAnalysisAPI
from cg.meta.workflow.taxprofiler import TaxprofilerAnalysisAPI
from cg.models.cg_config import CGConfig
from cg.store import Store
from cg.store.models import Case, Sample
from tests.conftest import StoreHelpers


class WorkflowPreAnalysisQCScenario:
    """
    A class representing a pre-analysis quality control scenario.

    This class encapsulates the logic for creating different types of analysis APIs
    based on the pipeline type, and for creating cases with different priorities and samples.

    Attributes:
        analysis_apis (dict[Pipeline, AnalysisAPI]): A mapping from pipeline types to their corresponding analysis API classes.
        pipeline (Pipeline): The pipeline type for this scenario.

    Methods:
        analysis_api: Returns the analysis API class for the current pipeline type.
        get_analysis_api: Returns an instance of the analysis API class for the current pipeline type, initialized with the given config.
        case_standard_priority: Creates and returns a case with standard priority and the given samples.
        case_express_priority: Creates and returns a case with express priority and the given samples.
        samples: Creates and returns a list of samples.
    """

    analysis_apis: dict[Pipeline, AnalysisAPI] = {
        Pipeline.BALSAMIC: BalsamicAnalysisAPI,
        Pipeline.BALSAMIC_QC: BalsamicQCAnalysisAPI,
        Pipeline.BALSAMIC_UMI: BalsamicUmiAnalysisAPI,
        Pipeline.MICROSALT: MicrosaltAnalysisAPI,
        Pipeline.MIP_DNA: MipDNAAnalysisAPI,
        Pipeline.MIP_RNA: MipRNAAnalysisAPI,
        Pipeline.TAXPROFILER: TaxprofilerAnalysisAPI,
        Pipeline.RNAFUSION: RnafusionAnalysisAPI,
        Pipeline.RAREDISEASE: RarediseaseAnalysisAPI,
    }

    def __init__(self, pipeline: Pipeline):
        self.pipeline = pipeline

    @property
    def analysis_api(self) -> AnalysisAPI:
        return self.analysis_apis[self.pipeline]

    def get_analysis_api(self, cg_config: CGConfig) -> AnalysisAPI:
        return self.analysis_api(config=cg_config, pipeline=self.pipeline)

    @staticmethod
    def case_standard_priority(
        base_store: Store, case_id: str, samples: list[Sample], helpers: StoreHelpers
    ):
        case_standard_priority: Case = helpers.add_case_with_samples(
            base_store=base_store, case_id=case_id, samples=samples, priority=Priority.standard
        )

        return case_standard_priority

    @staticmethod
    def case_express_priority(
        case_id: str, base_store: Store, samples: list[Sample], helpers: StoreHelpers
    ):
        case_express_priority: Case = helpers.add_case_with_samples(
            base_store=base_store, case_id=case_id, samples=samples, priority=Priority.express
        )
        return case_express_priority

    @staticmethod
    def samples(base_store: Store, helpers: StoreHelpers) -> list[Sample]:
        return [helpers.add_sample(base_store, reads=100) for _ in range(3)]


@pytest.mark.parametrize(
    "pre_analysis_qc_scenario,expected_qc",
    [
        (WorkflowPreAnalysisQCScenario(pipeline=Pipeline.BALSAMIC), BalsamicPreAnalysisQc),
        (WorkflowPreAnalysisQCScenario(pipeline=Pipeline.BALSAMIC_QC), BalsamicPreAnalysisQc),
        (WorkflowPreAnalysisQCScenario(pipeline=Pipeline.BALSAMIC_UMI), BalsamicPreAnalysisQc),
        (WorkflowPreAnalysisQCScenario(pipeline=Pipeline.MICROSALT), MicrobialPreAnalysisQc),
        (WorkflowPreAnalysisQCScenario(pipeline=Pipeline.MIP_DNA), MIPPreAnalysisQc),
        (WorkflowPreAnalysisQCScenario(pipeline=Pipeline.MIP_RNA), MIPPreAnalysisQc),
        (WorkflowPreAnalysisQCScenario(pipeline=Pipeline.TAXPROFILER), TaxProfilerPreAnalysisQc),
        (WorkflowPreAnalysisQCScenario(pipeline=Pipeline.RNAFUSION), RnafusionPreAnalysisQc),
        (WorkflowPreAnalysisQCScenario(pipeline=Pipeline.RAREDISEASE), RareDiseasePreAnalysisQc),
    ],
    ids=[
        "BALSAMIC",
        "BALSAMIC_QC",
        "BALSAMIC_UMI",
        "MICROSALT",
        "MIP_DNA",
        "MIP_RNA",
        "TAXPROFILER",
        "RNAFUSION",
        "RAREDISEASE",
    ],
)
def test_get_pre_analysis_quality_check_for_workflow(
    pre_analysis_qc_scenario: WorkflowPreAnalysisQCScenario,
    expected_qc: PreAnalysisQualityCheck,
    cg_context: CGConfig,
):
    # GIVEN a pre analysis qc scenario with an analysis api
    analysis_api: AnalysisAPI = pre_analysis_qc_scenario.get_analysis_api(cg_config=cg_context)

    # WHEN getting the pre analysis qc for the workflow
    pre_analysis_qc: PreAnalysisQualityCheck = get_pre_analysis_quality_check_for_workflow(
        analysis_api=analysis_api
    )
    # THEN assert that the correct pre analysis qc is returned

    assert pre_analysis_qc is expected_qc


@pytest.mark.parametrize(
    "pre_analysis_qc_scenario,expected_result",
    [
        (WorkflowPreAnalysisQCScenario(pipeline=Pipeline.BALSAMIC), True),
        (WorkflowPreAnalysisQCScenario(pipeline=Pipeline.MICROSALT), True),
        (WorkflowPreAnalysisQCScenario(pipeline=Pipeline.MIP_DNA), True),
        (WorkflowPreAnalysisQCScenario(pipeline=Pipeline.TAXPROFILER), True),
        (WorkflowPreAnalysisQCScenario(pipeline=Pipeline.RNAFUSION), True),
        (WorkflowPreAnalysisQCScenario(pipeline=Pipeline.RAREDISEASE), True),
    ],
    ids=[
        "BalsamicPreAnalysisQc_standard_priority",
        "MicrobialPreAnalysisQc_standard_priority",
        "MIPPreAnalysisQc_standard_priority",
        "TaxProfilerPreAnalysisQc_standard_priority",
        "RnafusionPreAnalysisQc_standard_priority",
        "RareDiseasePreAnalysisQc_standard_priority",
    ],
)
def test_sequencing_qc(
    pre_analysis_qc_scenario: WorkflowPreAnalysisQCScenario,
    expected_result: bool,
    case_id: str,
    cg_context: CGConfig,
    helpers: StoreHelpers,
):
    # GIVEN a pre analysis qc scenario with an analysis api
    analysis_api = pre_analysis_qc_scenario.get_analysis_api(cg_config=cg_context)
    # GIVEN a pre analysis quality checker
    pre_analysis_quality_checker = get_pre_analysis_quality_check_for_workflow(
        analysis_api=analysis_api
    )
    # GIVEN a case with standard priority and samples
    case: Case = pre_analysis_qc_scenario.case_standard_priority(
        base_store=cg_context.status_db,
        case_id=case_id,
        samples=pre_analysis_qc_scenario.samples(base_store=cg_context.status_db, helpers=helpers),
        helpers=helpers,
    )
    # WHEN instantiating the quality check
    paqc: PreAnalysisQualityCheck = pre_analysis_quality_checker(case)
    # WHEN checking the sequencing qc
    sequencing_qc: bool = paqc.sequencing_qc()
    # THEN assert that the correct pre analysis qc is returned
    assert sequencing_qc == expected_result


@pytest.mark.parametrize(
    "pre_analysis_qc_scenario,expected_result",
    [
        (WorkflowPreAnalysisQCScenario(pipeline=Pipeline.BALSAMIC), True),
        (WorkflowPreAnalysisQCScenario(pipeline=Pipeline.MIP_DNA), True),
        (WorkflowPreAnalysisQCScenario(pipeline=Pipeline.RNAFUSION), True),
        (WorkflowPreAnalysisQCScenario(pipeline=Pipeline.RAREDISEASE), True),
    ],
    ids=[
        "BalsamicPreAnalysisQc_express_priority",
        "MIPPreAnalysisQc_express_priority",
        "RnafusionPreAnalysisQc_express_priority",
        "RareDiseasePreAnalysisQc_express_priority",
    ],
)
def test_sequencing_qc_express_priority(
    pre_analysis_qc_scenario: WorkflowPreAnalysisQCScenario,
    expected_result: bool,
    case_id: str,
    cg_context: CGConfig,
    helpers: StoreHelpers,
):
    # GIVEN a pre analysis qc scenario with an analysis api
    analysis_api = pre_analysis_qc_scenario.get_analysis_api(cg_config=cg_context)
    # GIVEN a pre analysis quality checker
    pre_analysis_quality_checker = get_pre_analysis_quality_check_for_workflow(
        analysis_api=analysis_api
    )
    # GIVEN a case with standard priority and samples
    case: Case = pre_analysis_qc_scenario.case_express_priority(
        base_store=cg_context.status_db,
        case_id=case_id,
        samples=pre_analysis_qc_scenario.samples(base_store=cg_context.status_db, helpers=helpers),
        helpers=helpers,
    )
    # WHEN checking the sequencing qc
    sequencing_qc: bool = pre_analysis_quality_checker.run_qc(case=case)

    # THEN assert that the correct pre analysis qc is returned
    assert sequencing_qc == expected_result


@pytest.fixture
def case_with_ready_made_libraries():
    samples = [Sample(prep_category=PrepCategory.ready_made_library, reads=100) for _ in range(3)]
    return Case(samples=samples)


@pytest.fixture
def case_with_not_ready_made_libraries():
    samples = [
        Sample(prep_category=PrepCategory.not_ready_made_library, reads=100) for _ in range(3)
    ]
    return Case(samples=samples)


def test_all_samples_are_ready_made_libraries(
    case_with_ready_made_libraries, case_with_not_ready_made_libraries
):
    qc = FastqPreAnalysisQc(case_with_ready_made_libraries)
    assert qc.all_samples_are_ready_made_libraries() is True

    qc = FastqPreAnalysisQc(case_with_not_ready_made_libraries)
    assert qc.all_samples_are_ready_made_libraries() is False


def test_ready_made_library_qc(case_with_ready_made_libraries):
    qc = FastqPreAnalysisQc(case_with_ready_made_libraries)
    assert qc.ready_made_library_qc() is True


def test_fastq_sequencing_qc(case_with_ready_made_libraries, case_with_not_ready_made_libraries):
    qc = FastqPreAnalysisQc(case_with_ready_made_libraries)
    assert qc.sequencing_qc() is True

    qc = FastqPreAnalysisQc(case_with_not_ready_made_libraries)
    assert qc.sequencing_qc() is False
