from typing import List

from cg.models.mip.mip_config import MipBaseConfig, parse_config
from cg.models.mip.mip_metrics_deliverables import MetricsDeliverables
from cg.models.mip.mip_sample_info import MipBaseSampleInfo, parse_sample_info


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
    mip_config: MipBaseConfig = parse_config(mip_config_raw)
    sample_info: MipBaseSampleInfo = parse_sample_info(sampleinfo_raw)
    qc_metrics = MetricsDeliverables(**qcmetrics_raw)
    outdata = {
        "id_metrics": qc_metrics.id_metrics,
        "analysis_sex": {},
        "at_dropout": {},
        "case": mip_config.case_id,
        "duplicates": {},
        "gc_dropout": {},
        "genome_build": sample_info.genome_build,
        "insert_size_standard_deviation": {},
        "mapped_reads": {},
        "median_insert_size": {},
        "mip_version": sample_info.mip_version,
        "rank_model_version": sample_info.rank_model_version,
        "sample_ids": _get_sample_ids(mip_config=mip_config),
        "sv_rank_model_version": sample_info.sv_rank_model_version,
    }
    return outdata


def _get_sample_ids(mip_config: MipBaseConfig) -> List:
    sample_ids: list = []
    for sample_data in mip_config.samples:
        sample_ids.append(sample_data.sample_id)
    return sample_ids
