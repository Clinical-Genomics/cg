"""Helper functions for compress cli."""

import datetime as dt
import logging
import os
from math import ceil
from pathlib import Path
from typing import Iterator

from housekeeper.store.models import Bundle, Version

from cg.apps.housekeeper.hk import HousekeeperAPI
from cg.constants.compression import CRUNCHY_MIN_GB_PER_PROCESS, MAX_READS_PER_GB
from cg.constants.slurm import SlurmProcessing
from cg.meta.compress import CompressAPI
from cg.meta.compress.files import get_spring_paths
from cg.store.models import Case
from cg.store.store import Store
from cg.utils.date import get_date_days_ago

LOG = logging.getLogger(__name__)


def get_cases_to_process(
    days_back: int, store: Store, case_id: str | None = None
) -> list[Case] | None:
    """Return cases to process."""
    cases: list[Case] = []
    if case_id:
        case: Case = store.get_case_by_internal_id(case_id)
        if not case:
            LOG.warning(f"Could not find case {case_id}")
            return
        if case.is_compressible:
            cases.append(case)
    else:
        date_threshold: dt.datetime = get_date_days_ago(days_ago=days_back)
        cases: list[Case] = store.get_cases_to_compress(date_threshold=date_threshold)
    return cases


def set_memory_according_to_reads(
    sample_id: str, sample_reads: int | None = None, sample_process_mem: int | None = None
) -> int | None:
    """Set SLURM sample process memory depending on the number of sample reads if sample_process_mem is not set."""
    if sample_process_mem:
        return sample_process_mem
    if not sample_reads:
        LOG.debug(f"No reads recorded for sample: {sample_id}")
        return
    sample_process_mem: int = ceil((sample_reads / MAX_READS_PER_GB))
    if sample_process_mem < CRUNCHY_MIN_GB_PER_PROCESS:
        return CRUNCHY_MIN_GB_PER_PROCESS
    if CRUNCHY_MIN_GB_PER_PROCESS <= sample_process_mem < SlurmProcessing.MAX_NODE_MEMORY:
        return sample_process_mem
    return SlurmProcessing.MAX_NODE_MEMORY


def update_compress_api(
    compress_api: CompressAPI, dry_run: bool, hours: int = None, mem: int = None, ntasks: int = None
) -> None:
    """Update parameters in Compress API."""

    compress_api.set_dry_run(dry_run=dry_run)
    if mem:
        LOG.debug(f"Set Crunchy API SLURM mem to {mem}")
        compress_api.crunchy_api.slurm_memory = mem
    if hours:
        LOG.debug(f"Set Crunchy API SLURM hours to {hours}")
        compress_api.crunchy_api.slurm_hours = hours
    if ntasks:
        LOG.debug(f"Set Crunchy API SLURM number of tasks to {ntasks}")
        compress_api.crunchy_api.slurm_number_tasks = ntasks


# Functions to fix problematic spring files


def get_versions(hk_api: HousekeeperAPI, bundle_name: str = None) -> Iterator[Version]:
    """Generates versions from hk bundles.

    If no bundle name is given generate latest version for every bundle.
    """
    if bundle_name:
        bundle: Bundle = hk_api.bundle(bundle_name)
        if not bundle:
            LOG.info(f"Could not find bundle {bundle_name}")
            return
        bundles: list[Bundle] = [bundle]
    else:
        bundles: list[Bundle] = hk_api.bundles()

    for bundle in bundles:
        LOG.debug(f"Check for versions in {bundle.name}")
        last_version: Version = hk_api.last_version(bundle.name)
        if not last_version:
            LOG.warning(f"No bundle found for {bundle.name} in Housekeeper")
            return
        yield last_version


def get_true_dir(dir_path: Path) -> Path | None:
    """Loop over the files in a directory, if any symlinks are found return the parent dir of the
    origin file."""
    # Check if there are any links to fastq files in the directory
    for fastq_path in dir_path.rglob("*"):
        # Check if there are fastq symlinks that points to the directory where the spring
        # path is located
        if fastq_path.is_symlink():
            return Path(os.readlink(fastq_path)).parent
    LOG.info("Could not find any symlinked files")
    return None


def compress_sample_fastqs_in_cases(
    compress_api: CompressAPI,
    cases: list[Case],
    dry_run: bool,
    number_of_conversions: int,
    hours: int = None,
    mem: int = None,
    ntasks: int = None,
) -> None:
    """Compress sample FASTQs for samples in cases."""
    case_conversion_count: int = 0
    individuals_conversion_count: int = 0
    for case in cases:
        case_converted = True
        if case_conversion_count >= number_of_conversions:
            break

        LOG.debug(f"Searching for FASTQ files in case {case.internal_id}")
        if not case.links:
            continue
        for case_link in case.links:
            sample_process_mem: int | None = set_memory_according_to_reads(
                sample_process_mem=mem,
                sample_id=case_link.sample.internal_id,
                sample_reads=case_link.sample.reads,
            )
            update_compress_api(
                compress_api=compress_api,
                dry_run=dry_run,
                hours=hours,
                mem=sample_process_mem,
                ntasks=ntasks,
            )
            case_converted: bool = compress_api.compress_fastq(
                sample_id=case_link.sample.internal_id
            )
            if not case_converted:
                LOG.debug(f"skipping individual {case_link.sample.internal_id}")
                continue
            individuals_conversion_count += 1
        if case_converted:
            case_conversion_count += 1
            LOG.info(f"Considering case {case.internal_id} converted")
    LOG.info(
        f"{individuals_conversion_count} individuals in {case_conversion_count} (completed) cases where compressed"
    )


def correct_spring_paths(
    hk_api: HousekeeperAPI, bundle_name: str = None, dry_run: bool = False
) -> None:
    """Function that will be used as a one off thing.

    There has been a problem when there are symlinked fastq files that are sent for compression.
    In these cases the spring archive has been created in the same place as that the symlinks are
    pointing to. This function will find those cases and move the spring archives to the correct
    place as specified in housekeeper.
    """
    versions = get_versions(hk_api=hk_api, bundle_name=bundle_name)
    for version_obj in versions:
        spring_paths = get_spring_paths(version_obj)
        i = 0
        for i, compression_obj in enumerate(spring_paths, 1):
            # We are interested in fixing the cases where spring paths are in wrong location
            spring_path = compression_obj.spring_path
            if spring_path.exists():
                continue

            # true_dir is where the spring paths actually exists
            true_dir = get_true_dir(spring_path.parent)
            if not true_dir:
                LOG.info("Could not find location of spring files")
                continue

            true_spring_path = true_dir / spring_path.name
            true_spring_config_path = true_spring_path.with_suffix("").with_suffix(".json")
            if not (true_spring_path.exists() and true_spring_config_path.exists()):
                LOG.info("Could not find spring and/or spring metadata files, skipping")
                continue
            LOG.info(
                f"Moving existing spring file (and config) {true_spring_path} to hk bundle path {spring_path}"
            )
            if not dry_run:
                # We know from above that the spring path does not exist
                true_spring_path.replace(spring_path)
                true_spring_config_path.replace(compression_obj.spring_metadata_path)
        if i == 0:
            LOG.debug("Could not find any spring files")
