""" MIP specific functionality for storing files in Housekeeper """
import logging
from pathlib import Path

import ruamel.yaml

from cg.exc import AnalysisNotFinishedError
from cg.meta.store import base as store_base

LOG = logging.getLogger(__name__)


def add_mip_analysis(config_stream):
    """Gather information from MIP analysis to store."""
    config_raw = ruamel.yaml.safe_load(config_stream)
    config_data = parse_config(config_raw)
    sampleinfo_raw = ruamel.yaml.safe_load(Path(config_data["sampleinfo_path"]).open())
    sampleinfo_data = parse_sampleinfo(sampleinfo_raw)

    deliverables_raw = ruamel.yaml.safe_load(Path(config_raw["store_file"]).open())
    return store_base.build_bundle(config_data, sampleinfo_data, deliverables_raw)


def parse_config(data: dict) -> dict:
    """Parse MIP config file.

    Args:
        data (dict): raw YAML input from MIP analysis config file

    Returns:
        dict: parsed data
    """
    return {
        "email": data.get("email"),
        "case": data["case_id"],
        "samples": _get_sample_analysis_type(data),
        "is_dryrun": bool("dry_run_all" in data),
        "out_dir": data["outdata_dir"],
        "priority": data["slurm_quality_of_service"],
        "sampleinfo_path": data["sample_info_file"],
    }


def parse_sampleinfo(data: dict) -> dict:
    """Parse MIP sample info file.

    Args:
        data (dict): raw YAML input from MIP qc sample info file

    Returns:
        dict: parsed data
    """

    return {
        "date": data["analysis_date"],
        "is_finished": data["analysisrunstatus"] == "finished",
        "case": data["case"],
        "version": data["mip_version"],
    }


def _get_sample_analysis_type(data: dict) -> list:
    """
    Get analysis type for all samples in the MIP config file
    """
    return [
        {"id": sample_id, "type": analysis_type}
        for sample_id, analysis_type in data["analysis_type"].items()
    ]
