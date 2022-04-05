from cg.models.balsamic.analysis import BalsamicAnalysis, parse_balsamic_analysis
from cg.models.balsamic.config import BalsamicConfigJSON
from cg.models.balsamic.metrics import BalsamicTargetedQCMetrics


def test_instantiate_balsamic_analysis(balsamic_config_raw, balsamic_metrics_raw):
    """Tests BALSAMIC analysis instance creation"""

    # GIVEN a config and metrics dictionaries

    # WHEN instantiating a BALSAMIC analysis object
    balsamic_analysis = parse_balsamic_analysis(balsamic_config_raw, balsamic_metrics_raw)

    # THEN assert that it was successfully created
    assert isinstance(balsamic_analysis, BalsamicAnalysis)
    assert isinstance(balsamic_analysis.config, BalsamicConfigJSON)
    assert isinstance(balsamic_analysis.sample_metrics["ACC0000A1"], BalsamicTargetedQCMetrics)
