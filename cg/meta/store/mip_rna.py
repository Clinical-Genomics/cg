"""Builds MIP RNA bundle for linking in Housekeeper"""
import datetime as dt
import logging
from pathlib import Path

import ruamel.yaml

from cg.exc import (
    AnalysisNotFinishedError,
    AnalysisDuplicationError,
    BundleAlreadyAddedError,
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
    new_analysis = add_new_complete_analysis_record(
        bundle_data, case_obj, status, version_obj
    )
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

    deliverables_raw = ruamel.yaml.safe_load(
        Path(
            config_data["store_file"]
        ).open()
    )
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
        {
            "path": file["path"],
            "tags": sorted(
                list(
                    set(
                        [
                            file["format"],
                            file["id"],
                            file["step"],
                            file["tag"],
                            "rd-rna",
                        ]
                    )
                    - set([None])
                )
            ),
            "archive": False,
        }
        for file in deliverables["files"]
    ]

    return data


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
        "samples": [
            {"id": sample_id, "type": analysis_type}
            for sample_id, analysis_type in data["analysis_type"].items()
        ],
        "is_dryrun": bool("dry_run_all" in data),
        "out_dir": data["outdata_dir"],
        "priority": data["slurm_quality_of_service"],
        "sampleinfo_path": data["sample_info_file"],
    }


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


def get_case(bundle_obj, status):
    """ Get a case from the status database """
    case_obj = status.family(bundle_obj.name)
    return case_obj


def reset_case_action(case_obj):
    """ Resets action on case """
    case_obj.action = None


def add_new_complete_analysis_record(bundle_data, case_obj, status, version_obj):
    """Function to create and return a new analysis database record"""
    pipeline = case_obj.links[0].sample.data_analysis
    pipeline = pipeline if pipeline else "mip"

    if status.analysis(family=case_obj, started_at=version_obj.created_at):
        raise AnalysisDuplicationError(
            f"Analysis object already exists for {case_obj.internal_id} {version_obj.created_at}"
        )

    new_analysis = status.add_analysis(
        pipeline=pipeline,
        version=bundle_data["pipeline_version"],
        started_at=version_obj.created_at,
        completed_at=dt.datetime.now(),
        primary=(len(case_obj.analyses) == 0),
    )
    new_analysis.family = case_obj
    return new_analysis


def include_files_in_housekeeper(bundle_obj, hk_api, version_obj):
    """Function to include files in housekeeper"""
    hk_api.include(version_obj)
    hk_api.add_commit(bundle_obj, version_obj)
