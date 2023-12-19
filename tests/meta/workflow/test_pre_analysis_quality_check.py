import pytest

from cg.constants import Priority
from cg.constants.constants import Pipeline
from cg.meta.workflow.analysis import AnalysisAPI
from cg.meta.workflow.balsamic import BalsamicAnalysisAPI
from cg.meta.workflow.microsalt import MicrosaltAnalysisAPI
from cg.meta.workflow.mip import MipAnalysisAPI
from cg.meta.workflow.pre_analysis_quality_check import (
    BalsamicPreAnalysisQc,
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


class PreAnalysisQCScenario:
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
        Pipeline.MICROSALT: MicrosaltAnalysisAPI,
        Pipeline.MIP_DNA: MipAnalysisAPI,
        Pipeline.MIP_RNA: MipAnalysisAPI,
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
        (PreAnalysisQCScenario(pipeline=Pipeline.BALSAMIC), BalsamicPreAnalysisQc),
        (PreAnalysisQCScenario(pipeline=Pipeline.BALSAMIC_QC), BalsamicPreAnalysisQc),
        (PreAnalysisQCScenario(pipeline=Pipeline.BALSAMIC_UMI), BalsamicPreAnalysisQc),
        (PreAnalysisQCScenario(pipeline=Pipeline.MICROSALT), MicrobialPreAnalysisQc),
        (PreAnalysisQCScenario(pipeline=Pipeline.MIP_DNA), MIPPreAnalysisQc),
        (PreAnalysisQCScenario(pipeline=Pipeline.MIP_RNA), MIPPreAnalysisQc),
        (PreAnalysisQCScenario(pipeline=Pipeline.TAXPROFILER), TaxProfilerPreAnalysisQc),
        (PreAnalysisQCScenario(pipeline=Pipeline.RNAFUSION), RnafusionPreAnalysisQc),
        (PreAnalysisQCScenario(pipeline=Pipeline.RAREDISEASE), RareDiseasePreAnalysisQc),
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
    pre_analysis_qc_scenario: PreAnalysisQCScenario,
    expected_qc: PreAnalysisQualityCheck,
    cg_context: CGConfig,
):
    # GIVEN a pre analysis qc scenario with an analysis api
    analysis_api: AnalysisAPI = pre_analysis_qc_scenario.analysis_api(cg_config=cg_context)

    # WHEN getting the pre analysis qc for the workflow
    pre_analysis_qc: PreAnalysisQualityCheck = get_pre_analysis_quality_check_for_workflow(
        analysis_api=analysis_api
    )
    # THEN assert that the correct pre analysis qc is returned

    assert pre_analysis_qc is expected_qc


@pytest.mark.parametrize(
    "pre_analysis_qc_scenario,expected_result",
    [
        (PreAnalysisQCScenario(pipeline=Pipeline.BALSAMIC), True),
        (PreAnalysisQCScenario(pipeline=Pipeline.MICROSALT), True),
        (PreAnalysisQCScenario(pipeline=Pipeline.MIP_DNA), True),
        (PreAnalysisQCScenario(pipeline=Pipeline.TAXPROFILER), True),
        (PreAnalysisQCScenario(pipeline=Pipeline.RNAFUSION), True),
        (PreAnalysisQCScenario(pipeline=Pipeline.RAREDISEASE), True),
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
    pre_analysis_qc_scenario: PreAnalysisQCScenario,
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
    "pre_analysis_qc,expected_result",
    [
        (PreAnalysisQCScenario(pipeline=Pipeline.BALSAMIC), True),
        (PreAnalysisQCScenario(pipeline=Pipeline.MIP_DNA), True),
        (PreAnalysisQCScenario(pipeline=Pipeline.RNAFUSION), True),
        (PreAnalysisQCScenario(pipeline=Pipeline.RAREDISEASE), True),
    ],
    ids=[
        "BalsamicPreAnalysisQc_express_priority",
        "MIPPreAnalysisQc_express_priority",
        "RnafusionPreAnalysisQc_express_priority",
        "RareDiseasePreAnalysisQc_express_priority",
    ],
)
def test_sequencing_qc_express_priority(
    pre_analysis_qc_scenario: PreAnalysisQCScenario,
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
