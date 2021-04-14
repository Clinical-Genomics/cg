"""Commands to finish up after a demultiplex run"""
import logging
from pathlib import Path

import click

from cg.apps.demultiplex.demultiplex_api import DemultiplexingAPI
from cg.models.demultiplex.flowcell import Flowcell

LOG = logging.getLogger(__name__)


@click.group(name="finish")
def finish_group():
    pass


@finish_group.command(name="flowcell")
@click.argument("flowcell-directory", type=click.Path(file_okay=False, exists=True))
@click.option("--dry-run", is_flag=True)
@click.pass_context
def finish_flowcell(context: click.Context, flowcell_directory: click.Path, dry_run: bool):
    """Command to finish up a flowcell after demultiplexing"""
    flowcell = Flowcell(Path(str(flowcell_directory)))
    demultiplex_api: DemultiplexingAPI = context.obj["demultiplex_api"]
    if not demultiplex_api.is_demultiplexing_completed(flowcell=flowcell):
        LOG.warning("Demultiplex is not ready!")
        raise click.Abort
    unaligned_dir: Path = demultiplex_api.unaligned_dir_path(flowcell=flowcell)
    for sub_dir in unaligned_dir.iterdir():
        if not sub_dir.is_dir():
            LOG.debug("Skipping %s since it is not a directory", sub_dir)
            continue
        dir_name: str = sub_dir.name
        if dir_name in ["Stats", "Reports"]:
            continue
        if dir_name.startswith("Project_"):
            continue
        if dir_name == "indexcheck":
            project_dir: Path = unaligned_dir / "_".join(["Project", dir_name])
            LOG.info("Move index directory to %s", project_dir)
            if not dry_run:
                sub_dir.rename(project_dir)
            continue
        # We now know that the rest are folders with sample directories
        for sample_dir in sub_dir.iterdir():
            # First we add the flowcell id to sample name
            for fastq_file in sample_dir.iterdir():
                sample_name: str = fastq_file.name
                new_name: str = "_".join([flowcell.flowcell_id, sample_name])
                new_file: Path = Path(fastq_file.parent) / new_name
                LOG.info("Move fastq file %s to %s", fastq_file, new_file)
                if not dry_run:
                    fastq_file.rename(new_file)


        SAMPLE =$(basename ${SAMPLE_DIR})
        log
        "mv ${SAMPLE_DIR} ${PROJECT_DIR}/Sample_${SAMPLE}"
        mv ${SAMPLE_DIR} ${PROJECT_DIR} / Sample_${SAMPLE}


