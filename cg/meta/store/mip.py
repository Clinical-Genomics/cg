""" MIP specific functionality for storing files in Houskeeper """
from pathlib import Path
import ruamel.yaml

from cg.exc import (
    AnalysisNotFinishedError,
)
from cg.meta.store.base import parse_config, parse_sampleinfo, build_bundle


def add_analysis(config_stream):
    """Gather information from MIP analysis to store."""
    config_raw = ruamel.yaml.safe_load(config_stream)
    config_data = parse_config(config_raw)
    sampleinfo_raw = ruamel.yaml.safe_load(Path(config_data["sampleinfo_path"]).open())
    sampleinfo_data = parse_sampleinfo(sampleinfo_raw)

    if sampleinfo_data["is_finished"] is False:
        raise AnalysisNotFinishedError("analysis not finished")

    deliverables_raw = ruamel.yaml.safe_load(Path(config_raw["store_file"]).open())
    new_bundle = build_bundle(config_data, sampleinfo_data, deliverables_raw)

    return new_bundle
