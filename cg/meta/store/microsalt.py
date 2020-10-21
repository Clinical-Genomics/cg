""" Microsalt specific functionality for storing files in Housekeeper """
import datetime as dt
import logging
import os
import ruamel.yaml

from _io import TextIOWrapper

from cg.constants import HK_TAGS, MICROSALT_TAGS
from cg.meta.store import base as store_base

LOG = logging.getLogger(__name__)


def add_microbial_analysis(config_stream: TextIOWrapper) -> dict:
    """Gather information from microSALT analysis to store."""

    deliverables = ruamel.yaml.safe_load(config_stream)
    analysis_date = _get_date_from_deliverables_path(config_stream.name)
    new_bundle = build_microbial_bundle(deliverables, analysis_date)

    return new_bundle


def build_microbial_bundle(deliverables: dict, analysis_date: dt.date) -> dict:
    """Create a new bundle to store in Housekeeper"""

    project_name = _get_microbial_name(deliverables)
    files = store_base.deliverables_files(deliverables, analysis_type="microbial")

    data = {
        "name": str(project_name),
        "created": analysis_date,
        "files": files,
    }
    return data


def microbial_deliverables_files(deliverables: dict) -> list:
    """Get all deliverable files from the pipeline"""

    pipeline_tags = HK_TAGS["microbial"]
    analysis_type_tags = MICROSALT_TAGS
    files = store_base.parse_files(deliverables, pipeline_tags, analysis_type_tags)

    return files


def _get_microbial_name(deliverables: dict) -> str:
    """ Get microbial id from deliverables """
    for file_ in deliverables["files"]:
        if file_["tag"] == "sampleinfo":
            return file_["id"]
    return None


def _get_date_from_deliverables_path(deliverables_path: str) -> dt.date:
    """ Get date from deliverables path """
    return dt.datetime.fromtimestamp(int(os.path.getctime(deliverables_path)))
