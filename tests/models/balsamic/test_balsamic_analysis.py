from cg.constants.constants import Workflow
from cg.meta.workflow.balsamic import BalsamicAnalysisAPI
from cg.models.balsamic.config import BalsamicConfigJSON
from cg.models.balsamic.metrics import BalsamicTargetedQCMetrics, BalsamicWGSQCMetrics


def test_parse_analysis_tga(cg_context, balsamic_tga_config_raw, balsamic_tga_metrics_raw):
    """Tests BALSAMIC analysis instance creation"""

    # GIVEN a config and metrics dictionaries and a BALSAMIC analysis API
    balsamic_analysis_api = BalsamicAnalysisAPI(cg_context, Workflow.BALSAMIC)

    # WHEN instantiating a BALSAMIC analysis object
    balsamic_analysis = balsamic_analysis_api.parse_analysis(
        balsamic_tga_config_raw, balsamic_tga_metrics_raw
    )

    # THEN assert that it was successfully created
    assert isinstance(balsamic_analysis.balsamic_config, BalsamicConfigJSON)
    assert isinstance(balsamic_analysis.sample_metrics["ACC0000A1"], BalsamicTargetedQCMetrics)


def test_parse_analysis_wgs(cg_context, balsamic_wgs_config_raw, balsamic_wgs_metrics_raw):
    """Tests BALSAMIC analysis instance creation"""

    # GIVEN a config and metrics dictionaries and a BALSAMIC analysis API
    balsamic_analysis_api = BalsamicAnalysisAPI(cg_context, Workflow.BALSAMIC)

    # WHEN instantiating a BALSAMIC analysis object
    balsamic_analysis = balsamic_analysis_api.parse_analysis(
        balsamic_wgs_config_raw, balsamic_wgs_metrics_raw
    )

    # THEN assert that it was successfully created

    assert isinstance(balsamic_analysis.balsamic_config, BalsamicConfigJSON)
    assert isinstance(balsamic_analysis.sample_metrics["ACC0000A1"], BalsamicWGSQCMetrics)
