""" Base module for building bioinfo workflow bundles for linking in Housekeeper"""
import datetime as dt

from cg.exc import (
    AnalysisDuplicationError,
    PipelineUnknownError,
)


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


def reset_case_action(case_obj):
    """ Resets action on case """
    case_obj.action = None


def get_files(deliverables: dict, pipeline: list) -> list:
    """Get all deliverable files from the pipeline"""

    data = [
        {"path": file["path"], "tags": get_tags(file, pipeline), "archive": False}
        for file in deliverables["files"]
    ]

    return data


def get_tags(file: dict, pipeline_tags: list) -> list:
    """Get all tags for a file"""

    all_tags = [file["format"], file["id"], file["step"], file["tag"]]
    all_tags.extend(pipeline_tags)
    unique_tags = set(all_tags)
    only_existing_tags = unique_tags - set([None])
    sorted_tags = sorted(list(only_existing_tags))

    return sorted_tags
