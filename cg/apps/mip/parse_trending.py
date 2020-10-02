from cg.apps.mip import parse_sampleinfo, parse_qcmetrics


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
    outdata = _define_output_dict()

    _config(mip_config_raw, outdata)
    _qc_metrics(outdata, qcmetrics_raw)
    _qc_sample_info(outdata, sampleinfo_raw)

    return outdata


def _add_rank_model_version(outdata, sampleinfo_data):
    outdata["sv_rank_model_version"] = sampleinfo_data["sv_rank_model_version"]
    outdata["rank_model_version"] = sampleinfo_data["rank_model_version"]


def _qc_sample_info(outdata, sampleinfo_raw):
    sampleinfo_data = _parse_qc_sample_info_file(sampleinfo_raw)
    _add_mip_version(outdata, sampleinfo_data)
    _add_genome_build(outdata, sampleinfo_data)
    _add_rank_model_version(outdata, sampleinfo_data)


def _qc_metrics(outdata, qcmetrics_raw):
    qcmetrics_data = _parse_qc_metric_file_into_dict(qcmetrics_raw)
    _add_sample_level_info_from_qc_metric_file(outdata, qcmetrics_data)


def _config(mip_config_raw, outdata):
    config_data = _parse_raw_mip_config_into_dict(mip_config_raw)
    _add_case_id(config_data, outdata)
    _add_all_samples_from_mip_config(config_data, outdata)


def _add_genome_build(outdata, sampleinfo_data):
    outdata["genome_build"] = sampleinfo_data["genome_build"]


def _add_mip_version(outdata, sampleinfo_data):
    outdata["mip_version"] = sampleinfo_data["version"]


def _parse_qc_sample_info_file(sampleinfo_raw):
    sampleinfo_data = parse_sampleinfo.parse_sampleinfo(sampleinfo_raw)
    return sampleinfo_data


def _add_sample_level_info_from_qc_metric_file(outdata, qcmetrics_data):
    for sample_data in qcmetrics_data:
        _add_duplicate_reads(outdata, qcmetrics_data[sample_data])
        _add_mapped_reads(outdata, qcmetrics_data[sample_data])
        _add_predicted_sex(outdata, qcmetrics_data[sample_data])
        _add_dropout_rates(outdata, qcmetrics_data[sample_data])
        _add_insert_size_metrics(outdata, qcmetrics_data[sample_data])


def _add_dropout_rates(outdata, sample_data):
    outdata["at_dropout"] = sample_data["at_dropout"]
    outdata["gc_dropout"] = sample_data["gc_dropout"]


def _add_insert_size_metrics(outdata, sample_data):
    outdata["median_insert_size"] = sample_data["median_insert_size"]
    outdata["insert_size_standard_deviation"] = sample_data["insert_size_standard_deviation"]


def _add_predicted_sex(outdata, sample_data):
    outdata["analysis_sex"] = sample_data["predicted_sex"]


def _add_mapped_reads(outdata, sample_data):
    mapped_reads_percent = sample_data["mapped"] * 100
    outdata["mapped_reads"] = mapped_reads_percent


def _add_duplicate_reads(outdata, sample_data):
    duplicates_percent = sample_data["duplicates"] * 100
    outdata["duplicates"] = duplicates_percent


def _parse_qc_metric_file_into_dict(qcmetrics_raw):
    qcmetrics_data = parse_qcmetrics.parse_qcmetrics(qcmetrics_raw)
    return qcmetrics_data


def _parse_raw_mip_config_into_dict(mip_config_raw):
    config_data = parse_sampleinfo.parse_config(mip_config_raw)
    return config_data


def _define_output_dict():
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

    return outdata


def _add_all_samples_from_mip_config(config_data, outdata):
    for sample_data in config_data["samples"]:
        outdata["sample_ids"].append(sample_data["id"])


def _add_case_id(config_data, outdata):
    outdata["case"] = config_data["case"]
