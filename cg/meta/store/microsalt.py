""" MIP specific functionality for storing files in Houskeeper """
import datetime as dt
import logging

import ruamel.yaml

from cg.constants import HK_TAGS, MICROSALT_TAGS
from cg.exc import (
    BundleAlreadyAddedError,
    AnalysisDuplicationError,
)

DUMMY_MICROSALT_CASE = "dummymicrobe"
LOG = logging.getLogger(__name__)


def gather_files_and_bundle_in_housekeeper(config_stream, hk_api, status):
    """Function to gather files and bundle in housekeeper"""
    bundle_data = add_microbial_analysis(config_stream)

    results = hk_api.add_bundle(bundle_data)
    if results is None:
        raise BundleAlreadyAddedError("bundle already added")

    bundle_obj, version_obj = results

    microbial_order_obj = status.microbial_order(bundle_obj.name)

    new_analysis = add_new_analysis(bundle_data, microbial_order_obj, status, version_obj)
    version_date = version_obj.created_at.date()

    LOG.info("new bundle added: %s, version %s", bundle_obj.name, version_date)
    hk_api.include(version_obj)
    hk_api.add_commit(bundle_obj, version_obj)

    return new_analysis


def add_microbial_analysis(config_stream):
    """Gather information from microSALT analysis to store."""

    deliverables = ruamel.yaml.safe_load(config_stream)
    new_bundle = build_microbial_bundle(deliverables)

    return new_bundle


def build_microbial_bundle(deliverables: dict) -> dict:
    """Create a new bundle to store in Housekeeper"""

    project_name = _get_microbial_name(deliverables)
    files = microbial_deliverables_files(deliverables)

    data = {
        "name": project_name,
        "created": _get_date_from_results_path(deliverables, project_name),
        "files": files,
    }
    return data


def microbial_deliverables_files(deliverables: dict) -> list:
    """Get all deliverable files from the pipeline"""

    pipeline_tags = HK_TAGS["microsalt"]
    analysis_type_tags = MICROSALT_TAGS
    files = parse_microbial_files(deliverables, pipeline_tags, analysis_type_tags)

    return files


def parse_microbial_files(
    deliverables: dict, pipeline_tags: list, analysis_type_tags: dict
) -> list:
    """Get all files and their tags from the deliverables files"""

    parsed_files = []
    for file_ in deliverables["files"]:
        tag_map_key = (file_["step"],) if file_["tag"] is None else (file_["step"], file_["tag"])
        parsed_file = {
            "path": file_["path"],
            "tags": get_tags(file_, pipeline_tags, analysis_type_tags, tag_map_key),
            "archive": False,
            "tag_map_key": tag_map_key,
        }
        parsed_files.append(parsed_file)

        if file_["path_index"]:
            parsed_index_file = {
                "path": file_["path_index"],
                "tags": get_tags(
                    file_, pipeline_tags, analysis_type_tags, tag_map_key, is_index=True
                ),
                "archive": False,
                "tag_map_key": tag_map_key,
            }
            parsed_files.append(parsed_index_file)

    return parsed_files


def get_tags(
    file: dict, pipeline_tags: list, tag_map: dict, tag_map_key: tuple, is_index: bool = False
) -> list:
    """Get all tags for a file"""

    tags = {
        "format": file["format"],
        "id": file["id"],
        "step": file["step"],
        "tag": file["tag"],
    }

    tags["pipeline"] = pipeline_tags[0]
    tags["application"] = pipeline_tags[1] if len(pipeline_tags) > 1 else None

    tags = _convert_tags(tags, tag_map, tag_map_key, is_index)
    return tags


def _convert_tags(tags: dict, tag_map: dict, tag_map_key: tuple, is_index: bool = False) -> list:
    """ Convert tags from external deliverables tags to standard internal housekeeper tags """

    if is_index:
        mapped_tags = tag_map[tag_map_key]["index_tags"]
    else:
        mapped_tags = tag_map[tag_map_key]["tags"]
    converted_tags = [
        tags["format"],
        str(tags["id"]),
        tags["pipeline"],
    ]

    if tags["application"] is not None:
        converted_tags.append(tags["application"])

    for tag in mapped_tags:
        converted_tags.append(tag)

    return sorted(list(set(converted_tags)))


def add_new_analysis(bundle_data, microbial_order_obj, status, version_obj):
    """Function to create and return a new analysis database record"""

    pipeline = HK_TAGS["microsalt"]

    if status.microbial_analysis(
        microbial_order_id=microbial_order_obj.id, started_at=version_obj.created_at
    ):
        raise AnalysisDuplicationError(
            f"Analysis object already exists for {microbial_order_obj.internal_id} {version_obj.created_at}"
        )

    new_analysis = status.add_analysis(
        pipeline=pipeline,
        started_at=version_obj.created_at,
        completed_at=dt.datetime.now(),
        primary=(len(microbial_order_obj.analyses) == 0),
    )
    case_obj = status.family(DUMMY_MICROSALT_CASE)
    new_analysis.family = case_obj
    new_analysis.microbial_order = microbial_order_obj
    return new_analysis


def _get_microbial_name(deliverables: dict) -> str:
    """ Get microbial id from deliverables """
    for file_ in deliverables["files"]:
        if file_["tag"] == "sampleinfo":
            return file_["id"]


def _get_date_from_results_path(deliverables: dict, project_name: str) -> dt.datetime:
    """ Get date from results path """
    first_file, *_ = deliverables["files"]
    results_path = first_file["path"]
    partial_path, _ = results_path.split("sampleinfo")
    [_, timestamp, _] = partial_path.split("//")
    [_, date, time] = timestamp.split("_")
    [year, month, day] = list(map(int, date.split(".")))
    [hour, minutes, seconds] = list(map(int, time.split(".")))
    return dt.datetime(year, month, day, hour, minutes, seconds)
