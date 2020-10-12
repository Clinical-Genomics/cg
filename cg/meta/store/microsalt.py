""" Microsalt specific functionality for storing files in Housekeeper """
import datetime as dt
import logging
from pathlib import Path
import ruamel.yaml

from _io import TextIOWrapper

from cg.constants import HK_TAGS, MICROSALT_TAGS
import cg.meta.store.base as store_base

LOG = logging.getLogger(__name__)


def add_microbial_analysis(config_stream: TextIOWrapper) -> dict:
    """Gather information from microSALT analysis to store."""

    deliverables = ruamel.yaml.safe_load(config_stream)
    new_bundle = build_microbial_bundle(deliverables)

    return new_bundle


def build_microbial_bundle(deliverables: dict) -> dict:
    """Create a new bundle to store in Housekeeper"""

    project_name = _get_microbial_name(deliverables)
    files = store_base.deliverables_files(deliverables, analysis_type="microbial")

    data = {
        "name": str(project_name),
        "created": _get_date_from_results_path(deliverables),
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


def _get_date_from_results_path(deliverables: dict) -> dt.datetime:
    """ Get date from results path """
    first_file, *_ = deliverables["files"]
    results_dir = Path(first_file["path"]).parent.name
    [_, date, time] = results_dir.split("_")
    [year, month, day] = list(map(int, date.split(".")))
    [hour, minutes, seconds] = list(map(int, time.split(".")))
    return dt.datetime(year, month, day, hour, minutes, seconds)
