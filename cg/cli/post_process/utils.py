"""Utility functions for the post-process command."""

import logging

from pydantic import BaseModel, ConfigDict

from cg.exc import CgError
from cg.models.cg_config import CGConfig
from cg.services.run_devices.abstract_classes import PostProcessingService
from cg.services.run_devices.pacbio.post_processing_service import PacBioPostProcessingService
from cg.services.run_devices.run_names.service import RunNamesService
from cg.utils.mapping import get_item_by_pattern_in_source

LOG = logging.getLogger(__name__)

PATTERN_TO_DEVICE_MAP: dict[str, str] = {
    r"^r\d+_\d+_\d+/(1|2)_[^/]+$": "pacbio",
}


class UnprocessedRunInfo(BaseModel):
    name: str
    post_processing_service: PostProcessingService
    instrument: str
    model_config = ConfigDict(arbitrary_types_allowed=True)


def get_post_processing_service_from_run_name(
    context: CGConfig, run_name: str
) -> PacBioPostProcessingService:
    """Get the correct post-processing service based on the run name."""
    try:
        device: str = get_item_by_pattern_in_source(
            source=run_name, pattern_map=PATTERN_TO_DEVICE_MAP
        )
    except CgError as error:
        raise NameError(
            f"Run name {run_name} does not match with any known sequencing run name pattern"
        ) from error
    return getattr(context.post_processing_services, device)


def get_unprocessed_runs_info(context: CGConfig, instrument: str) -> list[UnprocessedRunInfo]:
    """Return a list of unprocessed runs for a given instrument or for all instruments."""
    runs: list[UnprocessedRunInfo] = []
    instruments_to_check: list[str] = _instruments_to_check(instrument)
    for instrument_name in instruments_to_check:
        run_names_service: RunNamesService = getattr(context.run_names_services, instrument_name)
        runs.extend(
            _get_unprocessed_runs_from_run_names(
                run_names=run_names_service.get_run_names(),
                post_processing_service=getattr(context.post_processing_services, instrument_name),
                instrument_name=instrument_name,
            )
        )
    return runs


def _instruments_to_check(instrument: str) -> list[str]:
    """Return a list of instruments to check for unprocessed runs."""
    possible_instruments: list[str] = ["pacbio"]  # Add more instruments here
    return [instrument] if instrument != "all" else possible_instruments


def _get_unprocessed_runs_from_run_names(
    run_names: list[str], post_processing_service: PostProcessingService, instrument_name
) -> list[UnprocessedRunInfo]:
    LOG.debug(f"Adding {instrument_name} run names to the post-processing list")
    runs: list[UnprocessedRunInfo] = []
    for name in run_names:
        if post_processing_service.is_run_processed(name):
            LOG.debug(f"Run {name} has already been post-processed. Skipping")
            continue
        if post_processing_service.can_post_processing_start(name):
            runs.append(
                UnprocessedRunInfo(
                    name=name,
                    post_processing_service=post_processing_service,
                    instrument=instrument_name,
                )
            )
    return runs
