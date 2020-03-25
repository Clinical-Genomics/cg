"""Builds MIP RNA bundle for linking in Housekeeper"""
import logging
from pathlib import Path

import ruamel.yaml

from cg.exc import AnalysisNotFinishedError, BundleAlreadyAddedError

from cg.meta.store.base import (
    get_case,
    reset_case_action,
    add_new_analysis,
    include_files_in_housekeeper,
)

LOG = logging.getLogger(__name__)


def gather_files_and_bundle_in_housekeeper(config_stream, hk_api, status):
    """Function to gather files and bundle in housekeeper"""
    bundle_data = add_analysis(config_stream)

    results = hk_api.add_bundle(bundle_data)
    if results is None:
        raise BundleAlreadyAddedError("bundle already added")
    bundle_obj, version_obj = results

    case_obj = get_case(bundle_obj, status)
    reset_case_action(case_obj)
    new_analysis = add_new_analysis(bundle_data, case_obj, status, version_obj)
    version_date = version_obj.created_at.date()
    LOG.info("new bundle added: %s, version %s", bundle_obj.name, version_date)
    include_files_in_housekeeper(bundle_obj, hk_api, version_obj)

    return new_analysis


def add_analysis(config_stream):
    """Gather information from MIP analysis to store."""
    config_raw = ruamel.yaml.safe_load(config_stream)
    config_data = parse_config(config_raw)
    sampleinfo_raw = ruamel.yaml.safe_load(Path(config_data["sampleinfo_path"]).open())
    sampleinfo_data = parse_sampleinfo(sampleinfo_raw)

    if sampleinfo_data["is_finished"] is False:
        raise AnalysisNotFinishedError("analysis not finished")

    breakpoint()
    deliverables_raw = ruamel.yaml.safe_load(Path(config_raw["store_file"]).open())
    new_bundle = build_bundle(config_data, sampleinfo_data, deliverables_raw)

    return new_bundle


def build_bundle(config_data: dict, sampleinfo_data: dict, deliverables: dict) -> dict:
    """Create a new bundle for RNA."""
    data = {
        "name": config_data["case"],
        "created": sampleinfo_data["date"],
        "pipeline_version": sampleinfo_data["version"],
        "files": get_files(deliverables),
    }
    return data


def get_files(deliverables: dict) -> dict:
    """Get all the files from the MIP RNA files."""

    data = [
        {"path": file["path"], "tags": get_tags(file), "archive": False,}
        for file in deliverables["files"]
    ]

    return data


def get_tags(file: dict) -> list:
    """Get all tags for a file"""
    breakpoint()

    all_tags = [file["format"], file["id"], file["step"], file["tag"], "rd-rna"]
    unique_tags = set(all_tags)
    only_existing_tags = unique_tags - set([None])
    sorted_tags = sorted(list(only_existing_tags))

    return sorted_tags


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


def _get_sample_analysis_type(data: dict) -> list:
    """
        get analysis type for all samples in the MIP config file
    """
    return [
        {"id": sample_id, "type": analysis_type}
        for sample_id, analysis_type in data["analysis_type"].items()
    ]


def parse_sampleinfo(data: dict) -> dict:
    """Parse MIP sample info file (RNA).

    Args:
        data (dict): raw YAML input from MIP qc sample info file (RNA)

    Returns:
        dict: parsed data
    """
    case = data["case"]

    sampleinfo_data = {
        "date": data["analysis_date"],
        "is_finished": data["analysisrunstatus"] == "finished",
        "case": case,
        "version": data["mip_version"],
    }

    return sampleinfo_data
