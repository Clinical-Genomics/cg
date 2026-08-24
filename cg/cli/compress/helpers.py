"""Helper functions for compress cli."""

import logging
import os
from pathlib import Path
from typing import Iterator

from housekeeper.store.models import Bundle, Version

from cg.apps.housekeeper.hk import HousekeeperAPI
from cg.constants import SequencingFileTag
from cg.meta.compress import CompressAPI
from cg.meta.compress.files import get_spring_paths
from cg.store.models import Case, Sample
from cg.store.store import Store
from cg.utils.date import get_date_days_ago

LOG = logging.getLogger(__name__)


def get_samples_available_for_compression(
    store: Store, housekeeper: HousekeeperAPI, age_limit_days: int, case_id: str | None = None
) -> list[Sample] | None:
    """Return samples available for compression."""

    if case_id:
        case: Case = store.get_case_by_internal_id_strict(case_id)
        sample_ids: list[str] = [sample.internal_id for sample in case.samples]
        if not sample_ids:
            LOG.warning(f"No samples found for {case_id}")
            return None

    else:
        sample_ids: list[str] = housekeeper.get_bundle_names_with_fastq_files()
        if not sample_ids:
            LOG.info(f"No bundles in Housekeeper with files tagged with {SequencingFileTag.FASTQ}")
            return None

    return store.get_compressible_samples_by_internal_ids(
        internal_ids=sample_ids, case_created_before_date=get_date_days_ago(age_limit_days)
    )


def update_compress_api(compress_api: CompressAPI, dry_run: bool) -> None:
    """Update parameters in Compress API."""
    compress_api.set_dry_run(dry_run=dry_run)


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


def compress_fastq_to_spring_for_samples(
    compress_api: CompressAPI,
    samples: list[Sample],
    sample_limit: int,
    dry_run: bool = False,
) -> None:
    """Compress the fastq files to spring for a list of samples."""
    if dry_run:
        update_compress_api(compress_api=compress_api, dry_run=dry_run)
        LOG.info("Dry-run activated - no samples will be submitted for compression")

    successful_submissions = 0
    for sample in samples:
        if sample_limit <= successful_submissions:
            break

        is_sample_submitted: bool = compress_api.compress_fastq(sample_id=sample.internal_id)
        if not is_sample_submitted:
            LOG.debug(f"Sample {sample.internal_id} not submitted for compression")
        else:
            successful_submissions += 1

    LOG.debug(f"Submitted a total of {successful_submissions} samples to compression")


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
