from typing import List, Optional


def get_case_from_config(config: dict) -> Optional[str]:
    """Get case id from config"""
    if "case_id" in config:
        return config["case_id"]
    if "family_id" in config:  # family for MIP<7
        return config["family_id"]
    return None


def get_dry_run_all(config: dict) -> bool:
    """Get dry_run_all from config"""
    if "dry_run_all" in config:
        return True
    return False


def get_sample_data_from_config(config: dict) -> List[dict]:
    """Get sample data from config"""
    samples = []
    for sample_id, analysis_type in config["analysis_type"].items():
        samples.append({"id": sample_id, "type": analysis_type})
    return samples


def parse_config(data: dict) -> dict:
    """Parse MIP config file

    Args:
        data (dict): raw YAML input from MIP analysis config file

    Returns:
        dict: parsed data
    """
    return {
        "email": data.get("email"),
        "case": get_case_from_config(config=data),
        "samples": get_sample_data_from_config(config=data),
        "config_path": data["config_file_analysis"],
        "is_dryrun": get_dry_run_all(config=data),
        "log_path": data["log_file"],
        "out_dir": data["outdata_dir"],
        "priority": data["slurm_quality_of_service"],
        "sampleinfo_path": data["sample_info_file"],
    }


def get_analysisrunstatus(sample_info: dict) -> bool:
    """Get analysis run status from sample info"""
    if sample_info["analysisrunstatus"] == "finished":
        return True
    return False


def get_sampleinfo_date(data: dict) -> str:
    """Get MIP sample info date

    Args:
        data (dict): raw YAML input from MIP qc sample info file

    Returns:
        str: analysis date
    """

    return data["analysis_date"]


def parse_sampleinfo_light(data: dict) -> dict:
    """Parse MIP sample info file and retrieve mip_version, date, and status

    Args:
        data (dict): raw YAML input from MIP qc sample info file

    Returns:
        dict: {'version': str, 'date': str, 'is_finished': str}


    """

    outdata = {
        "date": get_sampleinfo_date(data=data),
        "version": data["mip_version"],
        "is_finished": get_analysisrunstatus(sample_info=data),
    }

    return outdata


def get_case_from_sampleinfo(sample_info: dict) -> str:
    """Get case id from sampleinfo"""
    if "case" in sample_info:
        return sample_info["case"]
    if "family" in sample_info:  # family for MIP<7
        return sample_info["family"]
    return None


def get_rank_model_version(sample_info: dict, rank_model_type: str, step: str) -> str:
    """Get rank model version"""
    rank_model_version = None
    for key in ("recipe", "program"):
        if key in sample_info:
            rank_model_version = sample_info[key][step][rank_model_type]["version"]
            break
    return rank_model_version


def get_genome_build(sample_info: dict) -> str:
    """Get genome build"""
    genome_build = sample_info["human_genome_build"]
    return f"{genome_build['source']}{genome_build['version']}"


def parse_sampleinfo(data: dict) -> dict:
    """Parse MIP sample info file.

    Args:
        data (dict): raw YAML input from MIP qc sample info file

    Returns:
        dict: parsed data
    """
    outdata = {
        "date": get_sampleinfo_date(data=data),
        "genome_build": get_genome_build(sample_info=data),
        "case": get_case_from_sampleinfo(sample_info=data),
        "is_finished": get_analysisrunstatus(sample_info=data),
        "rank_model_version": get_rank_model_version(
            sample_info=data, rank_model_type="rank_model", step="genmod"
        ),
        "samples": [],
        "sv_rank_model_version": get_rank_model_version(
            sample_info=data, rank_model_type="sv_rank_model", step="sv_genmod"
        ),
        "version": data["mip_version"],
    }

    for sample_id in data["sample"].items():
        sample = {"id": sample_id}
        outdata["samples"].append(sample)

    return outdata
