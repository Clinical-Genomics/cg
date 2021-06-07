from cg.apps.mip import parse_qcmetrics
from cg.models.mip.mip_config import MipBaseConfig, parse_config
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
    outdata = {
        "analysis_sex": {},
        "at_dropout": {},
        "case": None,
        "duplicates": {},
        "gc_dropout": {},
        "genome_build": None,
        "rank_model_version": None,
        "insert_size_standard_deviation": {},
        "mapped_reads": {},
        "median_insert_size": {},
        "mip_version": None,
        "sample_ids": [],
    }

    _config(mip_config_raw=mip_config_raw, outdata=outdata)
    _qc_metrics(qcmetrics_raw=qcmetrics_raw, outdata=outdata)
    _qc_sample_info(sampleinfo_raw=sampleinfo_raw, outdata=outdata)

    return outdata


def _qc_sample_info(outdata: dict, sampleinfo_raw: dict) -> None:
    sample_info: MipBaseSampleInfo = parse_sample_info(sampleinfo_raw)
    outdata["genome_build"] = sample_info.genome_build
    outdata["mip_version"] = sample_info.mip_version
    outdata["rank_model_version"] = sample_info.rank_model_version
    outdata["sv_rank_model_version"] = sample_info.sv_rank_model_version


def _qc_metrics(outdata: dict, qcmetrics_raw: dict) -> None:
    qcmetrics_data = _parse_qc_metric_file_into_dict(qcmetrics_raw)
    _add_sample_level_info_from_qc_metric_file(outdata, qcmetrics_data)


def _config(mip_config_raw: dict, outdata: dict) -> None:
    mip_config: MipBaseConfig = parse_config(mip_config_raw)
    outdata["case"] = mip_config.case_id
    for sample_data in mip_config.samples:
        outdata["sample_ids"].append(sample_data.sample_id)


def _add_sample_level_info_from_qc_metric_file(outdata: dict, qcmetrics_data: dict) -> None:
    for sample_data in qcmetrics_data:
        _add_duplicate_reads(outdata, qcmetrics_data[sample_data])
        _add_mapped_reads(outdata, qcmetrics_data[sample_data])
        _add_predicted_sex(outdata, qcmetrics_data[sample_data])
        _add_dropout_rates(outdata, qcmetrics_data[sample_data])
        _add_insert_size_metrics(outdata, qcmetrics_data[sample_data])


def _add_dropout_rates(outdata: dict, sample_data: dict) -> None:
    outdata["at_dropout"][sample_data["id"]] = sample_data["at_dropout"]
    outdata["gc_dropout"][sample_data["id"]] = sample_data["gc_dropout"]


def _add_insert_size_metrics(outdata: dict, sample_data: dict) -> None:
    outdata["median_insert_size"][sample_data["id"]] = sample_data["median_insert_size"]
    outdata["insert_size_standard_deviation"][sample_data["id"]] = sample_data[
        "insert_size_standard_deviation"
    ]


def _add_predicted_sex(outdata: dict, sample_data: dict) -> None:
    outdata["analysis_sex"][sample_data["id"]] = sample_data["predicted_sex"]


def _add_mapped_reads(outdata: dict, sample_data: dict) -> None:
    mapped_reads_percent = sample_data["mapped"] * 100
    outdata["mapped_reads"][sample_data["id"]] = mapped_reads_percent


def _add_duplicate_reads(outdata: dict, sample_data: dict) -> None:
    duplicates_percent = sample_data["duplicates"] * 100
    outdata["duplicates"][sample_data["id"]] = duplicates_percent


def _parse_qc_metric_file_into_dict(qcmetrics_raw: dict) -> dict:
    qcmetrics_data = parse_qcmetrics.parse_qcmetrics(qcmetrics_raw)
    return qcmetrics_data
