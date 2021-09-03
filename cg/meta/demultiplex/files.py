import logging
import sys
from pathlib import Path

from cg.constants.demultiplexing import FASTQ_FILE_SUFFIXES
from cg.constants.symbols import UNDERSCORE

LOG = logging.getLogger(__name__)


def rename_index_dir(unaligned_dir: Path, dry_run: bool = False) -> None:
    """Rename the index directory by adding the prefix Project_"""
    for sub_dir in unaligned_dir.iterdir():
        if not sub_dir.is_dir():
            continue
        if sub_dir.name != "indexcheck":
            continue
        if sub_dir.name.startswith("Project_"):
            LOG.debug("%s is already renamed", sub_dir)
            continue
        index_directory: Path = unaligned_dir / "_".join(["Project", sub_dir.name])
        LOG.debug("Move index directory %s", sub_dir)
        if not dry_run:
            LOG.debug("Move directory to %s", index_directory)
            sub_dir.rename(index_directory)


def rename_project_directory(
    project_directory: Path, flowcell_id: str, dry_run: bool = False
) -> None:
    """Rename a project directory by adding the prefix Project_"""
    unaligned_directory: Path = project_directory.parent
    LOG.info("Check for Dragen fastq files in project directories.")
    if dragen_fastq_files_in_project_directory(project_directory):
        LOG.debug("Only Dragen fastq files found!")
        move_dragen_fastq_files(project_directory=project_directory, dry_run=dry_run)
        if dry_run:
            LOG.info("Can't continue dry run...")
            sys.exit()

    LOG.debug("Rename all sample directories in %s", unaligned_directory)
    for sample_dir in project_directory.iterdir():
        if sample_dir.name.startswith("Sample"):
            LOG.debug("%s is already renamed", sample_dir)
            continue
        rename_sample_directory(
            sample_directory=sample_dir, flowcell_id=flowcell_id, dry_run=dry_run
        )
    new_name: str = "_".join(["Project", project_directory.name])
    new_project_path: Path = unaligned_directory / new_name
    LOG.debug("Rename project dir %s", project_directory)
    if not dry_run:
        LOG.debug("Rename project dir to %s", new_project_path)
        project_directory.rename(new_project_path)


def move_dragen_fastq_files(project_directory: Path, dry_run: bool = False) -> None:
    """Move Dragen fastq files into sample directories"""

    for dragen_fastq_file in project_directory.iterdir():
        LOG.debug(
            "Derive sample name from fastq file %s: %s",
            dragen_fastq_file,
            get_dragen_sample_name(dragen_fastq_file),
        )
        dragen_sample_name: str = get_dragen_sample_name(dragen_fastq_file)
        LOG.debug("Create sample directory %s:", project_directory / dragen_sample_name)
        if not dry_run:
            (project_directory / dragen_sample_name).mkdir(exist_ok=True)
        target_directory: Path = project_directory / dragen_sample_name / dragen_fastq_file.name
        LOG.debug("Move fastq file into sample directory: %s", target_directory)
        if not dry_run:
            dragen_fastq_file.rename(target_directory)


def rename_sample_directory(
    sample_directory: Path, flowcell_id: str, dry_run: bool = False
) -> None:
    """Rename a sample dir and all fastq files in the sample dir

    Renaming of the sample dir means adding Sample_ as a prefix
    """
    project_directory: Path = sample_directory.parent
    LOG.debug("Renaming all fastq files in %s", sample_directory)
    for fastq_file in sample_directory.iterdir():
        rename_fastq_file(fastq_file=fastq_file, flowcell_id=flowcell_id, dry_run=dry_run)
    new_name: str = "_".join(["Sample", sample_directory.name])
    new_sample_directory: Path = project_directory / new_name
    LOG.debug("Renaming sample dir %s to %s", sample_directory, new_sample_directory)
    if not dry_run:
        sample_directory.rename(new_sample_directory)
        LOG.debug("Renamed sample dir to %s", new_sample_directory)


def rename_fastq_file(fastq_file: Path, flowcell_id: str, dry_run: bool = False) -> None:
    """Rename a fastq file by appending the flowcell id as a prefix"""
    new_name: str = "_".join([flowcell_id, fastq_file.name])
    new_file: Path = Path(fastq_file.parent) / new_name
    LOG.debug("Renaming fastq file %s to %s", fastq_file, new_file)
    if not dry_run:
        fastq_file.rename(new_file)
        LOG.debug("Renamed fastq file to %s", new_file)


def dragen_fastq_files_in_project_directory(project_directory: Path) -> bool:
    """Checks if the project directory contains Dragen fastq files instead of sample directories"""
    return all(file_.suffixes == FASTQ_FILE_SUFFIXES for file_ in project_directory.iterdir())


def get_dragen_sample_name(dragen_fastq_file: Path) -> str:
    """Derives the sample name from a dragen fastq file"""
    return dragen_fastq_file.name.split(UNDERSCORE)[0]
