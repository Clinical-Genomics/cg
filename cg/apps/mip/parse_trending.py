from cg.apps.mip import parse_qcmetrics, parse_sampleinfo


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


def _add_rank_model_version(outdata: dict, sampleinfo_data: dict) -> None:
    outdata["sv_rank_model_version"] = sampleinfo_data["sv_rank_model_version"]
    outdata["rank_model_version"] = sampleinfo_data["rank_model_version"]


def _qc_sample_info(outdata: dict, sampleinfo_raw: dict) -> None:
    sampleinfo_data = _parse_qc_sample_info_file(sampleinfo_raw)
    _add_mip_version(outdata, sampleinfo_data)
    _add_genome_build(outdata, sampleinfo_data)
    _add_rank_model_version(outdata, sampleinfo_data)


def _qc_metrics(outdata: dict, qcmetrics_raw: dict) -> None:
    qcmetrics_data = _parse_qc_metric_file_into_dict(qcmetrics_raw)
    _add_sample_level_info_from_qc_metric_file(outdata, qcmetrics_data)


def _config(mip_config_raw: dict, outdata: dict) -> dict:
    config_data = _parse_raw_mip_config_into_dict(mip_config_raw)
    _add_case_id(config_data, outdata)
    _add_all_samples_from_mip_config(config_data, outdata)
    return config_data


def _add_genome_build(outdata: dict, sampleinfo_data: dict) -> None:
    outdata["genome_build"] = sampleinfo_data["genome_build"]


def _add_mip_version(outdata: dict, sampleinfo_data: dict) -> None:
    outdata["mip_version"] = sampleinfo_data["version"]


def _parse_qc_sample_info_file(sampleinfo_raw: dict) -> dict:
    return parse_sampleinfo.parse_sampleinfo(sampleinfo_raw)


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


def _parse_raw_mip_config_into_dict(mip_config_raw: dict) -> dict:
    config_data = parse_sampleinfo.parse_config(mip_config_raw)
    return config_data


def _add_all_samples_from_mip_config(config_data: dict, outdata: dict) -> None:
    for sample_data in config_data["samples"]:
        outdata["sample_ids"].append(sample_data["id"])


def _add_case_id(config_data: dict, outdata: dict) -> None:
    outdata["case"] = config_data["case"]
