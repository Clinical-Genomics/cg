"""Helper functions for compress cli"""
import logging
import os
from pathlib import Path
from typing import Iterator

from cg.apps.housekeeper.hk import HousekeeperAPI
from cg.exc import CaseNotFoundError
from cg.meta.compress import CompressAPI
from cg.meta.compress.files import get_spring_paths
from cg.store import Store
from housekeeper.store import models as hk_models

LOG = logging.getLogger(__name__)


def get_fastq_individuals(store: Store, case_id: str = None) -> Iterator[str]:
    """Fetch individual ids from cases that are ready for SPRING compression"""
    case_obj = store.family(case_id)
    if not case_obj:
        LOG.error("Could not find case %s", case_id)
        raise CaseNotFoundError("")

    for link_obj in case_obj.links:
        yield link_obj.sample.internal_id


def update_compress_api(
    compress_api: CompressAPI, dry_run: bool, ntasks: int = None, mem: int = None
) -> None:
    """Update parameters in compress api"""

    compress_api.set_dry_run(dry_run)
    if ntasks:
        LOG.info("Set ntasks to %s", ntasks)
        compress_api.ntasks = ntasks
    if mem:
        LOG.info("Set mem to %s", ntasks)
        compress_api.mem = mem


# Functions to fix problematic spring files


def get_versions(hk_api: HousekeeperAPI, bundle_name: str = None) -> Iterator[hk_models.Version]:
    """Generates versions from hk bundles

    If no bundle name is given generate latest version for every bundle
    """
    if bundle_name:
        bundle = hk_api.bundle(bundle_name)
        if not bundle:
            LOG.info("Could not find bundle %s", bundle_name)
            return
        bundles = [bundle]
    else:
        bundles = hk_api.bundles()

    for bundle in bundles:
        LOG.debug("Check for versions in %s", bundle.name)
        last_version = hk_api.last_version(bundle.name)
        if not last_version:
            LOG.warning("No bundle found for %s in housekeeper", bundle.name)
            return
        yield last_version


def get_true_dir(dir_path: Path) -> Path:
    """Loop over the files in a directory, if any symlinks are found return the parent dir of the
    origin file"""
    # Check if there are any links to fastq files in the directory
    for fastq_path in dir_path.rglob("*"):
        # Check if there are fastq symlinks that points to the directory where the spring
        # path is located
        if fastq_path.is_symlink():
            true_dir = Path(os.readlink(fastq_path)).parent
            return true_dir
    LOG.info("Could not find any symlinked files")
    return None


def correct_spring_paths(
    hk_api: HousekeeperAPI, bundle_name: str = None, dry_run: bool = False
) -> None:
    """Function that will be used as a one off thing

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

            spring_config_path = compression_obj.spring_metadata_path
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
                "Moving existing spring file (and config) %s to hk bundle path %s",
                true_spring_path,
                spring_path,
            )
            if not dry_run:
                # We know from above that the spring path does not exist
                true_spring_path.replace(spring_path)
                true_spring_config_path.replace(spring_config_path)
        if i == 0:
            LOG.debug("Could not find any spring files")
