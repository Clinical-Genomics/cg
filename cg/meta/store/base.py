"""Base module for building bioinfo workflow bundles for linking in Housekeeper"""
import datetime as dt
import logging
from typing import List

from _io import TextIOWrapper
from housekeeper.store import models as hk_models

from cg.apps.housekeeper.hk import HousekeeperAPI
from cg.constants import HK_TAGS, MICROSALT_TAGS, MIP_DNA_TAGS, MIP_RNA_TAGS, Pipeline
from cg.exc import (
    AnalysisDuplicationError,
    BundleAlreadyAddedError,
    MandatoryFilesMissing,
    PipelineUnknownError,
)
from cg.meta.store import mip as store_mip
from cg.store import Store, models
from cg.store.utils import reset_case_action

ANALYSIS_TYPE_TAGS = {
    "wgs": MIP_DNA_TAGS,
    "wes": MIP_DNA_TAGS,
    "wts": MIP_RNA_TAGS,
    "microsalt": MICROSALT_TAGS,
}
LOG = logging.getLogger(__name__)


def gather_files_and_bundle_in_housekeeper(
    config_stream: TextIOWrapper, hk_api: HousekeeperAPI, status: Store, workflow: Pipeline
) -> models.Analysis:
    """Function to gather files and bundle in housekeeper"""

    add_analysis = {
        Pipeline.MIP_DNA: store_mip.add_mip_analysis,
    }
    bundle_data = add_analysis[workflow](config_stream)

    results = hk_api.add_bundle(bundle_data)
    if results is None:
        raise BundleAlreadyAddedError("bundle already added")

    bundle_obj, version_obj = results

    case_obj = {
        Pipeline.MIP_DNA: status.family(bundle_obj.name),
    }

    reset_case_action(case_obj[workflow])
    new_analysis = add_new_analysis(bundle_data, case_obj[workflow], status, version_obj)
    version_date = version_obj.created_at.date()

    LOG.info("new bundle added: %s, version %s", bundle_obj.name, version_date)
    hk_api.include(version_obj)
    hk_api.add_commit(bundle_obj, version_obj)

    return new_analysis


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


def add_new_analysis(
    bundle_data: dict,
    case_obj: models.Family,
    status: Store,
    version_obj: hk_models.Version,
) -> models.Analysis:
    """Function to create and return a new analysis database record"""

    try:
        pipeline = Pipeline(case_obj.data_analysis)
    except ValueError:
        raise PipelineUnknownError(f"No pipeline specified in {case_obj}")

    if status.analysis(family=case_obj, started_at=version_obj.created_at):
        raise AnalysisDuplicationError(
            f"Analysis object already exists for {case_obj.internal_id} {version_obj.created_at}"
        )

    new_analysis = status.add_analysis(
        pipeline=pipeline,
        version=bundle_data.get("pipeline_version"),
        started_at=version_obj.created_at,
        completed_at=dt.datetime.now(),
        primary=(len(case_obj.analyses) == 0),
    )
    new_analysis.family = case_obj
    return new_analysis


def deliverables_files(deliverables: dict, analysis_type: str) -> list:
    """Get all deliverable files from the pipeline"""
    pipeline_tags = HK_TAGS[str(analysis_type)]
    analysis_type_tags = ANALYSIS_TYPE_TAGS[str(analysis_type)]
    files = parse_files(deliverables, pipeline_tags, analysis_type_tags)
    _check_mandatory_tags(files, analysis_type_tags)
    return files


def _is_deliverables_tags_missing_in_analysis_tags(
    analysis_type_tags: dict, deliverables_tag_map: tuple
) -> bool:
    """Check if deliverable tags are represented in analysis tags """
    if deliverables_tag_map in analysis_type_tags:
        return False
    return True


def parse_files(deliverables: dict, pipeline_tags: list, analysis_type_tags: dict) -> list:
    """ Get all files and their tags from the deliverables file """

    parsed_files = []
    for file_ in deliverables["files"]:
        deliverables_tag_map = (
            (file_["step"],) if file_["tag"] is None else (file_["step"], file_["tag"])
        )
        if _is_deliverables_tags_missing_in_analysis_tags(
            analysis_type_tags=analysis_type_tags, deliverables_tag_map=deliverables_tag_map
        ):
            continue
        parsed_file = {
            "path": file_["path"],
            "tags": get_tags(file_, pipeline_tags, analysis_type_tags, deliverables_tag_map),
            "archive": False,
            "deliverables_tag_map": deliverables_tag_map,
        }
        parsed_files.append(parsed_file)

        if file_["path_index"]:
            parsed_index_file = {
                "path": file_["path_index"],
                "tags": get_tags(
                    file_, pipeline_tags, analysis_type_tags, deliverables_tag_map, is_index=True
                ),
                "archive": False,
                "deliverables_tag_map": deliverables_tag_map,
            }
            parsed_files.append(parsed_index_file)

    return parsed_files


def get_tags(
    file: dict,
    pipeline_tags: list,
    analysis_type_tags: dict,
    deliverables_tag_map: tuple,
    is_index: bool = False,
) -> List[str]:
    """Get all tags for a file"""

    tags = {"id": str(file["id"])}
    tags["pipeline"] = pipeline_tags[0]
    tags["application"] = pipeline_tags[1] if len(pipeline_tags) > 1 else None

    return _convert_deliverables_tags_to_hk_tags(
        tags, analysis_type_tags, deliverables_tag_map, is_index
    )


def _convert_deliverables_tags_to_hk_tags(
    tags: dict, analysis_type_tags: dict, deliverables_tag_map: tuple, is_index: bool = False
) -> List[str]:
    """
    Filter and convert tags from external deliverables tags to standard internal housekeeper
    tags
    """

    if is_index:
        mapped_tags = analysis_type_tags[deliverables_tag_map]["index_tags"]
    else:
        mapped_tags = analysis_type_tags[deliverables_tag_map]["tags"]
    converted_tags = [tags["id"], tags["pipeline"]]

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
    deliverable_tags = [file_["deliverables_tag_map"] for file_ in files]
    mandatory_tags = [tag for tag in pipeline_tags if pipeline_tags[tag]["is_mandatory"]]

    tags_are_missing, missing_tags = _determine_missing_tags(mandatory_tags, deliverable_tags)

    if tags_are_missing:
        raise MandatoryFilesMissing(
            f"Mandatory files are missing! These are the missing tags: {missing_tags}."
        )


def _determine_missing_tags(mandatory_tags: list, found_tags: list) -> tuple:
    """
    Determines if mandatory tags are missing and hence if files are missing in the
    deliverables, and returns any missing tags
    """

    missing_tags = set(mandatory_tags) - set(found_tags)
    are_tags_missing = bool(len(missing_tags) > 0)

    return are_tags_missing, missing_tags
