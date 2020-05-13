""" Base module for building bioinfo workflow bundles for linking in Housekeeper"""
import datetime as dt

from cg.constants import HK_TAGS, MIP_DNA_TAGS
from cg.exc import (
    AnalysisDuplicationError,
    PipelineUnknownError,
    MandatoryFilesMissing,
)


def add_new_analysis(bundle_data, case_obj, status, version_obj):
    """Function to create and return a new analysis database record"""

    breakpoint()
    pipeline = case_obj.links[0].sample.data_analysis

    if not pipeline:
        raise PipelineUnknownError(f"No pipeline specified in {case_obj}")

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


def reset_case_action(case_obj):
    """ Resets action on case """

    case_obj.action = None


def get_files(deliverables: dict, pipeline: list) -> list:
    """Get all deliverable files from the pipeline"""

    files = _get_files_non_index(deliverables, pipeline)
    index_files = _get_files_index(deliverables, pipeline)

    files.extend(index_files)

    _check_mandatory_tags(files)
    _convert_tags(files)

    return files


def _get_files_non_index(deliverables: dict, pipeline: list) -> list:
    """ Get all files that are not index files from the deliverables file """

    return [
        {"path": file["path"], "tags": get_tags(file, pipeline), "archive": False}
        for file in deliverables["files"]
    ]


def _get_files_index(deliverables: dict, pipeline: list) -> list:
    """ Get all index files from the deliverables file """

    return [
        {"path": file["path_index"], "tags": get_tags(file, pipeline_tags), "archive": False,}
        for file in deliverables["files"]
        if file["path_index"]
    ]


def get_tags(file: dict, pipeline_tags: list) -> list:
    """Get all tags for a file"""

    all_tags = [file["format"], file["id"], file["step"], file["tag"]]
    all_tags.extend(pipeline_tags)
    unique_tags = set(all_tags)
    only_existing_tags = unique_tags - set([None])
    sorted_tags = sorted(list(only_existing_tags))

    return sorted_tags


def build_bundle(config_data: dict, analysisinfo_data: dict, deliverables: dict) -> dict:
    """Create a new bundle to store in Housekeeper"""

    pipeline = config_data["samples"][0]["type"]
    pipeline_tag = HK_TAGS[pipeline]

    data = {
        "name": config_data["case"],
        "created": analysisinfo_data["date"],
        "pipeline_version": analysisinfo_data["version"],
        "files": get_files(deliverables, pipeline_tag),
    }
    return data


def _convert_tags(data: list):
    """ Convert tags from deliverables tags to MIP standard tags """

    for deliverables_tags, mip_tags in MIP_TAGS.items():
        for file in data:
            if all(tag in file["tags"] for tag in deliverables_tags):
                tags_filtered = list(filter(lambda x: x not in deliverables_tags, file["tags"]))
                converted_tags = tags_filtered + pipeline_tags["tags"]
                file["tags"] = converted_tags


def _check_mandatory_tags(files: list):
    """
        Check if all the mandatory tags are present for the files to be added to Housekeeper.
        Raise an exception if not.
    """

    all_deliverable_tags = [file["tags"] for file in files]
    all_mandatory_tags = [tag for tag in MIP_TAGS if MIP_TAGS[tag]["is_mandatory"]]
    deliverable_tags = _flatten(all_deliverable_tags)
    mandatory_tags = _flatten(all_mandatory_tags)

    tags_are_missing, missing_tags = _determine_missing_files(mandatory_tags, deliverable_tags)

    if tags_are_missing:
        raise MandatoryFilesMissing(
            f"Mandatory files are missing! These are the missing tags: {missing_tags}."
        )


def _determine_missing_files(mandatory_tags: set, found_tags: set) -> tuple:
    """Determines if mandatory are missing, and which ones"""

    missing_tags = mandatory_tags.difference(found_tags)
    are_tags_missing = bool(len(missing_tags) > 0)

    return are_tags_missing, missing_tags


def _flatten(nested_list: list) -> set:
    """ Flattens a nested tag list and returns all unique tags"""

    return {tag for tag_list in nested_list for tag in tag_list}
