"""Builds balsamic bundle for linking in Housekeeper"""
import datetime as dt
import logging
import os
import shutil

import ruamel.yaml
from cg.exc import AnalysisDuplicationError
from pathlib import Path

LOG = logging.getLogger(__name__)


def gather_files_and_bundle_in_housekeeper(config_stream, hk_api, status, case_obj):
    """Function to gather files and bundle in housekeeper"""

    bundle_data = _add_analysis(config_stream, case_obj)

    results = hk_api.add_bundle(bundle_data)
    if not results:
        raise AnalysisDuplicationError("analysis version already added")
    bundle_obj, version_obj = results

    _reset_analysis_action(case_obj)
    new_analysis = _create_analysis(bundle_data, case_obj, status, version_obj)
    version_date = version_obj.created_at.date()
    LOG.info(f"new bundle added: {bundle_obj.name}, version {version_date}")
    _include_files_in_housekeeper(bundle_obj, hk_api, version_obj)
    return new_analysis


def _include_files_in_housekeeper(bundle_obj, hk_api, version_obj):
    """Function to include files in housekeeper"""
    hk_api.include(version_obj)
    hk_api.store.add_commit(bundle_obj, version_obj)


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
    case_obj.action = None


def _add_analysis(config_stream, case_obj):
    """Gather information from balsamic analysis to store."""
    with Path(config_stream).open() as in_stream:
        meta_raw = ruamel.yaml.safe_load(in_stream)
    new_bundle = _build_bundle(
        meta_raw, name=case_obj.internal_id, created=dt.datetime.now(), version="1"
    )
    return new_bundle


def _build_bundle(meta_data: dict, name: str, created: dt.datetime, version: str) -> dict:
    """Create a new bundle."""
    data = {
        "name": name,
        "created": created,
        "pipeline_version": version,
        "files": _get_files(meta_data),
    }
    return data


def _get_files(meta_data: dict) -> list:
    """Get all the files from the balsamic files."""

    paths = {}
    for tag in meta_data["files"]:
        for path_str in meta_data["files"][tag]:
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
    shutil.make_archive(path, "gztar", path)
    return f"{path}.tgz"
