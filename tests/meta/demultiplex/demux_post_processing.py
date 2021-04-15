import logging
from pathlib import Path
from typing import Optional

from cg.apps.demultiplex.demultiplex_api import DemultiplexingAPI
from cg.models.demultiplex.flowcell import Flowcell

LOG = logging.getLogger(__name__)


class DemuxPostProcessingAPI:
    def __init__(self):
        self.dry_run = False

    @staticmethod
    def rename_index_dir(unaligned_dir: Path, dry_run: bool = False) -> None:
        """Rename the index directory by adding the prefix Project_"""
        for sub_dir in unaligned_dir.iterdir():
            if not sub_dir.is_dir():
                continue
            if sub_dir.name != "indexcheck":
                continue
            index_directory: Path = unaligned_dir / "_".join(["Project", sub_dir.name])
            LOG.info("Move index directory %s", sub_dir)
            if not dry_run:
                LOG.info("Move directory to %s", index_directory)
                sub_dir.rename(index_directory)

    def rename_files(self, unaligned_dir: Path, flowcell: Flowcell) -> None:
        """Rename the files according to how we want to have it after demultiplexing is ready"""
        self.rename_index_dir(unaligned_dir=unaligned_dir, dry_run=self.dry_run)
        for sub_dir in unaligned_dir.iterdir():
            if not sub_dir.is_dir():
                LOG.debug("Skipping %s since it is not a directory", sub_dir)
                continue
            dir_name: str = sub_dir.name
            if dir_name in ["Stats", "Reports"]:
                LOG.debug("Skipping %s dir %s", dir_name, sub_dir)
                continue
            if dir_name.startswith("Project_"):
                LOG.debug("Skipping already renamed project dir %s", sub_dir)
                continue
            # We now know that the rest of the directories are project directories
            project_directory: Path = sub_dir
            for sample_directory in project_directory.iterdir():
                self.rename_sample_directory(
                    sample_directory=sample_directory, flowcell_id=flowcell.flowcell_id
                )

    def rename_project_directory(self, project_directory: Path) -> None:
        """Rename a project directory by adding the prefix Project_"""
        unaligned_directory: Path = project_directory.parent
        new_name: str = "_".join(["Project", project_directory.name])
        new_project_path: Path = unaligned_directory / new_name
        LOG.info("Rename project dir %s", project_directory)
        if not self.dry_run:
            LOG.info("Rename project dir to %s", new_project_path)
            project_directory.rename(new_project_path)

    def rename_sample_directory(self, sample_directory: Path, flowcell_id: str) -> None:
        """Rename a sample dir and all fastq files in the sample dir

        Renaming of the sample dir means adding Sample_ as a prefix
        """
        project_directory: Path = sample_directory.parent
        LOG.info("Renaming all fastq files in %s", sample_directory)
        for fastq_file in sample_directory.iterdir():
            self.rename_fastq_file(fastq_file, flowcell_id=flowcell_id)
        new_name: str = "_".join(["Sample", sample_directory.name])
        new_sample_directory: Path = project_directory / new_name
        LOG.info("Rename sample dir %s", sample_directory)
        if not self.dry_run:
            LOG.info("Rename sample dir to %s", new_sample_directory)
            sample_directory.rename(new_sample_directory)

    def rename_fastq_file(self, fastq_file: Path, flowcell_id: str) -> None:
        """Rename a fastq file by appending the flowcell id as a prefix"""
        new_name: str = "_".join([flowcell_id, fastq_file.name])
        new_file: Path = Path(fastq_file.parent) / new_name
        LOG.info("Rename fastq file %s", fastq_file, new_file)
        if not self.dry_run:
            LOG.info("Rename fastq file to %s", new_file)
            fastq_file.rename(new_file)
