from cg.models.mip.mip_config import MipBaseConfig
from cg.models.mip.mip_metrics_deliverables import MetricsDeliverables
from cg.models.mip.mip_sample_info import MipBaseSampleInfo


def parse_mip_analysis(mip_config_raw: dict, qcmetrics_raw: dict, sampleinfo_raw: dict) -> dict:
    """Parse the output analysis files from MIP for adding info
    to trend database

    Args:
        mip_config_raw (dict): raw YAML input from MIP analysis config file
        qcmetrics_raw (dict): raw YAML input from MIP analysis qc metric file
        sampleinfo_raw (dict): raw YAML input from MIP analysis qc sample info file
    Returns:
        dict: parsed data
    """
    mip_config: MipBaseConfig = MipBaseConfig(**mip_config_raw)
    qc_metrics = MetricsDeliverables(**qcmetrics_raw)
    sample_info: MipBaseSampleInfo = MipBaseSampleInfo(**sampleinfo_raw)

    outdata = {
        "case": mip_config.case_id,
        "genome_build": sample_info.genome_build,
        "id_metrics": qc_metrics.id_metrics,
        "mip_version": sample_info.mip_version,
        "rank_model_version": sample_info.rank_model_version,
        "sample_ids": mip_config.sample_ids,
        "sv_rank_model_version": sample_info.sv_rank_model_version,
    }
    return outdata
