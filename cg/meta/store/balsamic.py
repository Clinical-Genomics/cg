"""Builds balsamic bundle for linking in Housekeeper"""
import datetime as dt
import logging
import os
import shutil
from pathlib import Path

import ruamel.yaml
from cg.exc import AnalysisDuplicationError

LOG = logging.getLogger(__name__)


def gather_files_and_bundle_in_housekeeper(
    config_path, deliverables_file, hk_api, status, case_obj
):
    """Function to create a bundle for an analysis in housekeeper"""

    bundle_data = _add_analysis(config_path, deliverables_file, case_obj)

    results = hk_api.add_bundle(bundle_data)
    if not results:
        raise AnalysisDuplicationError("analysis version already added")
    bundle_obj, version_obj = results

    _reset_analysis_action(case_obj)
    new_analysis = _create_analysis(bundle_data, case_obj, status, version_obj)
    version_date = version_obj.created_at.date()
    LOG.info("new bundle added: %s, version %s", bundle_obj.name, version_date)
    _include_files_in_housekeeper(bundle_obj, hk_api, version_obj)
    return new_analysis


def _include_files_in_housekeeper(bundle_obj, hk_api, version_obj):
    """Function to include files in housekeeper"""
    hk_api.include(version_obj)
    hk_api.add_commit(bundle_obj, version_obj)


def _create_analysis(bundle_data, case_obj, status, version_obj):
    """Function to create and return a new analysis database record"""
    pipeline = case_obj.links[0].sample.data_analysis
    pipeline = pipeline if pipeline else "balsamic"

    if status.analysis(family=case_obj, started_at=version_obj.created_at):
        raise AnalysisDuplicationError(
            f"Analysis object already exists for {case_obj.internal_id}{version_obj.created_at}"
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


def _reset_analysis_action(case_obj):
    """Resets desired action on the case"""
    case_obj.action = None


def parse_created(config_data: dict) -> dt.datetime:
    """Parse out analysis creation data from analysis"""
    datetime_str = config_data["analysis"]["config_creation_date"]
    return dt.datetime.strptime(datetime_str, "%Y-%m-%d %H:%M")


def parse_version(config_data: dict) -> dt.datetime:
    """Parse out analysis pipeline version from analysis"""
    return config_data["analysis"]["BALSAMIC_version"]


def _add_analysis(config_path, deliverables_file, case_obj):
    """Gather information from balsamic analysis to store."""

    with Path(config_path).open() as config_stream:
        config_raw = ruamel.yaml.safe_load(config_stream)
        created = parse_created(config_raw)
        version = parse_version(config_raw)

    with Path(deliverables_file).open() as in_stream:
        deliverables_raw = ruamel.yaml.safe_load(in_stream)

    new_bundle = _build_bundle(
        deliverables_raw, name=case_obj.internal_id, created=created, version=version
    )
    return new_bundle


def _build_bundle(deliverables_data: dict, name: str, created: dt.datetime, version: str) -> dict:
    """Create a new bundle."""
    data = {
        "name": name,
        "created": created,
        "pipeline_version": version,
        "files": _get_files(deliverables_data),
    }
    return data


def _get_files(deliverables_data: dict) -> list:
    """Get all the files from the balsamic files."""

    paths = {}
    for tag in deliverables_data["files"]:
        for path_str in deliverables_data["files"][tag]:
            path = Path(path_str).name
            if path in paths.keys():
                paths[path]["tags"].append(tag)
            else:
                paths[path] = {"tags": [tag], "full_path": path_str}

    data = []
    for path_item in paths.values():
        path = path_item["full_path"]
        tags = path_item["tags"]
        if os.path.isdir(path):
            path = compress_directory(path)

        data.append({"path": path, "tags": tags, "archive": False})
    return data


def compress_directory(path):
    """Compresses a directory and returns its compressed name"""
    return shutil.make_archive(path, "gztar", path, logger=LOG)
