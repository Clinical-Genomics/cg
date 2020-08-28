""" MIP specific functionality for storing files in Houskeeper """
import logging
from pathlib import Path
import ruamel.yaml

from cg.exc import (
    AnalysisNotFinishedError,
    BundleAlreadyAddedError,
)
from cg.meta.store.base import (
    build_bundle,
    add_new_analysis,
)
from cg.store.utils import reset_case_action

LOG = logging.getLogger(__name__)


def gather_files_and_bundle_in_housekeeper(config_stream, hk_api, status):
    """Function to gather files and bundle in housekeeper"""
    bundle_data = add_analysis(config_stream)

    results = hk_api.add_bundle(bundle_data)
    if results is None:
        raise BundleAlreadyAddedError("bundle already added")

    bundle_obj, version_obj = results

    case_obj = status.family(bundle_obj.name)

    reset_case_action(case_obj)
    new_analysis = add_new_analysis(bundle_data, case_obj, status, version_obj)
    version_date = version_obj.created_at.date()

    LOG.info("new bundle added: %s, version %s", bundle_obj.name, version_date)
    hk_api.include(version_obj)
    hk_api.add_commit(bundle_obj, version_obj)

    return new_analysis


def add_analysis(config_stream):
    """Gather information from MIP analysis to store."""
    config_raw = ruamel.yaml.safe_load(config_stream)
    config_data = parse_config(config_raw)
    sampleinfo_raw = ruamel.yaml.safe_load(Path(config_data["sampleinfo_path"]).open())
    sampleinfo_data = parse_sampleinfo(sampleinfo_raw)

    if sampleinfo_data["is_finished"] is False:
        raise AnalysisNotFinishedError("analysis not finished")

    deliverables_raw = ruamel.yaml.safe_load(Path(config_raw["store_file"]).open())
    new_bundle = build_bundle(config_data, sampleinfo_data, deliverables_raw)

    return new_bundle


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

    sampleinfo_data = {
        "date": data["analysis_date"],
        "is_finished": data["analysisrunstatus"] == "finished",
        "case": data["case"],
        "version": data["mip_version"],
    }

    return sampleinfo_data


def _get_sample_analysis_type(data: dict) -> list:
    """
    Get analysis type for all samples in the MIP config file
    """
    return [
        {"id": sample_id, "type": analysis_type}
        for sample_id, analysis_type in data["analysis_type"].items()
    ]
