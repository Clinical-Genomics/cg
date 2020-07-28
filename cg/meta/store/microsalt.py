""" MIP specific functionality for storing files in Houskeeper """
import logging

# from pathlib import Path
import ruamel.yaml

from cg.constants import HK_TAGS, MICROSALT_TAGS
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
    bundle_data = add_microbial_analysis(config_stream)

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


def add_microbial_analysis(config_stream):
    """Gather information from microSALT analysis to store."""
    deliverables = ruamel.yaml.safe_load(config_stream)

    new_bundle = build_microbial_bundle(deliverables)

    return new_bundle


def build_microbial_bundle(deliverables: dict) -> dict:
    """Create a new bundle to store in Housekeeper"""

    data = {
        "name": "name_stub",
        "created": "date_stub",
        "files": microbial_deliverables_files(deliverables),
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
        tags["id"],
        tags["pipeline"],
    ]

    if tags["application"] is not None:
        converted_tags.append(tags["application"])

    for tag in mapped_tags:
        converted_tags.append(tag)

    return sorted(list(set(converted_tags)))
