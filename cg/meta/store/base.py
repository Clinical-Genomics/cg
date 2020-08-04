""" Base module for building bioinfo workflow bundles for linking in Housekeeper"""
import datetime as dt

from cg.constants import HK_TAGS, MIP_DNA_TAGS, MIP_RNA_TAGS

from cg.exc import (
    AnalysisDuplicationError,
    PipelineUnknownError,
    MandatoryFilesMissing,
)

ANALYSIS_TYPE_TAGS = {
    "wgs": MIP_DNA_TAGS,
    "wes": MIP_DNA_TAGS,
    "wts": MIP_RNA_TAGS,
}


def build_bundle(config_data: dict, analysisinfo_data: dict, deliverables: dict) -> dict:
    """Create a new bundle to store in Housekeeper"""

    analysis_type = config_data["samples"][0]["type"]

    data = {
        "name": config_data["case"],
        "created": analysisinfo_data["date"],
        "pipeline_version": analysisinfo_data["version"],
        "files": deliverables_files(deliverables, analysis_type),
    }
    return data


def add_new_analysis(bundle_data, case_obj, status, version_obj):
    """Function to create and return a new analysis database record"""

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


def deliverables_files(deliverables: dict, analysis_type: str) -> list:
    """Get all deliverable files from the pipeline"""

    pipeline_tags = HK_TAGS[analysis_type]
    analysis_type_tags = ANALYSIS_TYPE_TAGS[analysis_type]

    files = parse_files(deliverables, pipeline_tags, analysis_type_tags)
    _check_mandatory_tags(files, analysis_type_tags)

    return files


def parse_files(deliverables: dict, pipeline_tags: list, analysis_type_tags: dict) -> list:
    """ Get all files and their tags from the deliverables file """

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
    """ Filter and convert tags from external deliverables tags to standard internal housekeeper tags """

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


def _check_mandatory_tags(files: list, pipeline_tags: dict):
    """
        Check if all the mandatory tags are present for the files to be added to Housekeeper.
        Raise an exception if not.
    """
    deliverable_tags = [file_["tag_map_key"] for file_ in files]
    mandatory_tags = [tag for tag in pipeline_tags if pipeline_tags[tag]["is_mandatory"]]

    tags_are_missing, missing_tags = _determine_missing_tags(mandatory_tags, deliverable_tags)

    if tags_are_missing:
        raise MandatoryFilesMissing(
            f"Mandatory files are missing! These are the missing tags: {missing_tags}."
        )


def _determine_missing_files(mandatory_tags: list, found_tags: list) -> tuple:
    """Determines if mandatory are files missing in the deliverables, and which ones"""

    missing_tags = set(mandatory_tags) - set(found_tags)
    are_tags_missing = bool(len(missing_tags) > 0)

    return are_tags_missing, missing_tags
