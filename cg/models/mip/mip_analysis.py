from typing import List

from pydantic import BaseModel

from cg.models.mip.mip_config import MipBaseConfig
from cg.models.mip.mip_metrics_deliverables import ParsedMetrics, MetricsDeliverables
from cg.models.mip.mip_sample_info import MipBaseSampleInfo


class MipAnalysis(BaseModel):
    case: str
    genome_build: str
    sample_id_metrics: List[ParsedMetrics]
    mip_version: str
    rank_model_version: str
    sample_ids: List[str]
    sv_rank_model_version: str


def parse_mip_analysis(
    mip_config_raw: dict, qc_metrics_raw: dict, sample_info_raw: dict
) -> MipAnalysis:
    """Parse the output analysis files from MIP

    Args:
        mip_config_raw (dict): raw YAML input from MIP analysis config file
        qc_metrics_raw (dict): raw YAML input from MIP analysis qc metric file
        sample_info_raw (dict): raw YAML input from MIP analysis qc sample info file
    Returns:
        MipAnalysis: parsed MIP analysis data
    """
    mip_config: MipBaseConfig = MipBaseConfig(**mip_config_raw)
    qc_metrics = MetricsDeliverables(**qc_metrics_raw)
    sample_info: MipBaseSampleInfo = MipBaseSampleInfo(**sample_info_raw)

    return MipAnalysis(
        case=mip_config.case_id,
        genome_build=sample_info.genome_build,
        sample_id_metrics=qc_metrics.sample_id_metrics,
        mip_version=sample_info.mip_version,
        rank_model_version=sample_info.rank_model_version,
        sample_ids=mip_config.sample_ids,
        sv_rank_model_version=sample_info.sv_rank_model_version,
    )
