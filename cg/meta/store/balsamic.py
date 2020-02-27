"""Builds balsamic bundle for linking in Housekeeper"""
import datetime
import datetime as dt
import logging
import ruamel.yaml
from cg.exc import AnalysisDuplicationError

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
    meta_raw = ruamel.yaml.safe_load(config_stream)
    new_bundle = _build_bundle(
        meta_raw, name=case_obj.internal_id, created=datetime.datetime.now(), version="1"
    )
    return new_bundle


def _build_bundle(meta_data: dict, name: str, created: datetime, version: str) -> dict:
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

    data = []
    for tag in meta_data["files"]:
        paths = meta_data["files"][tag]
        for path in paths:
            data.append({"path": path, "tags": [tag], "archive": False})

    return data
