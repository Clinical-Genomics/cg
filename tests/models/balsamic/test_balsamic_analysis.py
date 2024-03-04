from cg.constants.constants import Workflow
from cg.meta.workflow.balsamic import BalsamicAnalysisAPI
from cg.models.balsamic.analysis import BalsamicAnalysis
from cg.models.balsamic.config import BalsamicConfigJSON
from cg.models.balsamic.metrics import BalsamicTargetedQCMetrics


def test_instantiate_balsamic_analysis(cg_context, balsamic_config_raw, balsamic_metrics_raw):
    """Tests BALSAMIC analysis instance creation"""

    # GIVEN a config and metrics dictionaries and a BALSAMIC analysis API
    balsamic_analysis_api = BalsamicAnalysisAPI(cg_context, Workflow.BALSAMIC)

    # WHEN instantiating a BALSAMIC analysis object
    balsamic_analysis = balsamic_analysis_api.parse_analysis(
        balsamic_config_raw, balsamic_metrics_raw
    )

    # THEN assert that it was successfully created
    assert isinstance(balsamic_analysis, BalsamicAnalysis)
    assert isinstance(balsamic_analysis.config, BalsamicConfigJSON)
    assert isinstance(balsamic_analysis.sample_metrics["ACC0000A1"], BalsamicTargetedQCMetrics)
