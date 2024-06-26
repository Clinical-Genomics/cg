"""Backup related CLI commands."""

import logging
from pathlib import Path
from typing import Iterable

import click
import housekeeper.store.models as hk_models

from cg.apps.housekeeper.hk import HousekeeperAPI
from cg.apps.slurm.slurm_api import SlurmAPI
from cg.cli.utils import CLICK_CONTEXT_SETTINGS
from cg.constants.cli_options import DRY_RUN
from cg.constants.constants import FlowCellStatus
from cg.constants.housekeeper_tags import SequencingFileTag
from cg.exc import (
    DsmcAlreadyRunningError,
    FlowCellAlreadyBackedUpError,
    FlowCellEncryptionError,
    FlowCellError,
    PdcError,
)
from cg.meta.backup.backup import BackupAPI, SpringBackupAPI
from cg.meta.backup.pdc import PdcAPI
from cg.meta.encryption.encryption import (
    EncryptionAPI,
    FlowCellEncryptionAPI,
    SpringEncryptionAPI,
)
from cg.meta.tar.tar import TarAPI
from cg.models.cg_config import CGConfig
from cg.models.run_devices.illumina_run_directory_data import (
    IlluminaRunDirectoryData,
    get_sequencing_runs_from_path,
)
from cg.store.models import Flowcell, Sample
from cg.store.store import Store

LOG = logging.getLogger(__name__)


@click.group(context_settings=CLICK_CONTEXT_SETTINGS)
@click.pass_obj
def backup(context: CGConfig):
    """Backup utilities"""
    pass


@backup.command("flow-cells")
@DRY_RUN
@click.pass_obj
def backup_flow_cells(context: CGConfig, dry_run: bool):
    """Back-up flow cells."""
    pdc_api = context.pdc_api
    pdc_api.dry_run = dry_run
    status_db: Store = context.status_db
    flow_cells: list[IlluminaRunDirectoryData] = get_sequencing_runs_from_path(
        sequencing_run_dir=Path(context.run_instruments.illumina.sequencing_runs_dir)
    )
    for flow_cell in flow_cells:
        db_flow_cell: Flowcell | None = status_db.get_flow_cell_by_name(flow_cell_name=flow_cell.id)
        flow_cell_encryption_api = FlowCellEncryptionAPI(
            binary_path=context.encryption.binary_path,
            dry_run=dry_run,
            encryption_dir=Path(context.encryption.encryption_dir),
            flow_cell=flow_cell,
            pigz_binary_path=context.pigz.binary_path,
            slurm_api=SlurmAPI(),
            sbatch_parameter=context.backup.slurm_flow_cell_encryption.dict(),
            tar_api=TarAPI(binary_path=context.tar.binary_path, dry_run=dry_run),
        )
        try:
            pdc_api.start_flow_cell_backup(
                db_flow_cell=db_flow_cell,
                flow_cell_encryption_api=flow_cell_encryption_api,
                status_db=status_db,
            )
        except (
            DsmcAlreadyRunningError,
            FlowCellAlreadyBackedUpError,
            FlowCellEncryptionError,
            PdcError,
        ) as error:
            logging.error(f"{error}")


@backup.command("encrypt-flow-cells")
@DRY_RUN
@click.pass_obj
def encrypt_flow_cells(context: CGConfig, dry_run: bool):
    """Encrypt flow cells."""
    status_db: Store = context.status_db
    flow_cells: list[IlluminaRunDirectoryData] = get_sequencing_runs_from_path(
        sequencing_run_dir=Path(context.run_instruments.illumina.sequencing_runs_dir)
    )
    for flow_cell in flow_cells:
        db_flow_cell: Flowcell | None = status_db.get_flow_cell_by_name(flow_cell_name=flow_cell.id)
        if db_flow_cell and db_flow_cell.has_backup:
            LOG.debug(f"Flow cell: {flow_cell.id} is already backed-up")
            continue
        flow_cell_encryption_api = FlowCellEncryptionAPI(
            binary_path=context.encryption.binary_path,
            dry_run=dry_run,
            encryption_dir=Path(context.encryption.encryption_dir),
            flow_cell=flow_cell,
            pigz_binary_path=context.pigz.binary_path,
            slurm_api=SlurmAPI(),
            sbatch_parameter=context.backup.slurm_flow_cell_encryption.dict(),
            tar_api=TarAPI(binary_path=context.tar.binary_path, dry_run=dry_run),
        )
        try:
            flow_cell_encryption_api.start_encryption()
        except (FlowCellError, FlowCellEncryptionError) as error:
            logging.error(f"{error}")


@backup.command("fetch-flow-cell")
@click.option("-f", "--flow-cell-id", help="Retrieve a specific flow cell, ex. 'HCK2KDSXX'")
@DRY_RUN
@click.pass_obj
def fetch_flow_cell(context: CGConfig, dry_run: bool, flow_cell_id: str | None = None):
    """Fetch the first flow cell in the requested queue from backup"""

    pdc_api = context.pdc_api
    pdc_api.dry_run = dry_run
    encryption_api = EncryptionAPI(binary_path=context.encryption.binary_path, dry_run=dry_run)
    tar_api = TarAPI(binary_path=context.tar.binary_path, dry_run=dry_run)
    context.meta_apis["backup_api"] = BackupAPI(
        encryption_api=encryption_api,
        pdc_archiving_directory=context.backup.pdc_archiving_directory,
        status=context.status_db,
        tar_api=tar_api,
        pdc_api=pdc_api,
        flow_cells_dir=context.run_instruments.illumina.sequencing_runs_dir,
        dry_run=dry_run,
    )
    backup_api: BackupAPI = context.meta_apis["backup_api"]

    status_api: Store = context.status_db
    flow_cell: Flowcell | None = (
        status_api.get_flow_cell_by_name(flow_cell_name=flow_cell_id) if flow_cell_id else None
    )

    if not flow_cell and flow_cell_id:
        LOG.error(f"{flow_cell_id}: not found in database")
        raise click.Abort

    if not flow_cell_id:
        LOG.info("Fetching first flow cell in queue")

    retrieval_time: float | None = backup_api.fetch_flow_cell(flow_cell=flow_cell)

    if retrieval_time:
        hours = retrieval_time / 60 / 60
        LOG.info(f"Retrieval time: {hours:.1}h")
        return

    if not dry_run and flow_cell:
        LOG.info(f"{flow_cell}: updating flow cell status to {FlowCellStatus.REQUESTED}")
        flow_cell.status = FlowCellStatus.REQUESTED
        status_api.session.commit()


@backup.command("archive-spring-files")
@DRY_RUN
@click.pass_context
@click.pass_obj
def archive_spring_files(config: CGConfig, context: click.Context, dry_run: bool):
    """Archive spring files to PDC"""
    housekeeper_api: HousekeeperAPI = config.housekeeper_api
    LOG.info("Getting all spring files from Housekeeper.")
    spring_files: Iterable[hk_models.File] = housekeeper_api.files(
        tags=[SequencingFileTag.SPRING]
    ).filter(hk_models.File.path.contains(f"{config.environment}/{config.demultiplex.out_dir}"))
    for spring_file in spring_files:
        LOG.info(f"Attempting encryption and PDC archiving for file {spring_file.path}")
        if Path(spring_file.path).exists():
            context.invoke(archive_spring_file, spring_file_path=spring_file.path, dry_run=dry_run)
        else:
            LOG.warning(
                f"Spring file {spring_file.path} found in Housekeeper, but not on disk! Archiving process skipped!"
            )


@backup.command("archive-spring-file")
@click.argument("spring-file-path", type=click.Path(exists=True))
@DRY_RUN
@click.pass_obj
def archive_spring_file(config: CGConfig, spring_file_path: str, dry_run: bool):
    """Archive a spring file to PDC"""
    housekeeper_api: HousekeeperAPI = config.housekeeper_api
    pdc_api: PdcAPI = PdcAPI(binary_path=config.pdc.binary_path, dry_run=dry_run)
    encryption_api: SpringEncryptionAPI = SpringEncryptionAPI(
        binary_path=config.encryption.binary_path,
        dry_run=dry_run,
    )
    spring_backup_api: SpringBackupAPI = SpringBackupAPI(
        encryption_api=encryption_api,
        hk_api=housekeeper_api,
        pdc_api=pdc_api,
        dry_run=dry_run,
    )
    LOG.debug("Start spring encryption/backup")
    spring_backup_api.encrypt_and_archive_spring_file(Path(spring_file_path))


@backup.command("retrieve-spring-files")
@DRY_RUN
@click.option("-s", "--sample-id", "object_type", flag_value="sample", type=str)
@click.option("-c", "--case-id", "object_type", flag_value="case", type=str)
@click.option("-f", "--flow-cell-id", "object_type", flag_value="run_devices", type=str)
@click.argument("identifier", type=str)
@click.pass_context
@click.pass_obj
def retrieve_spring_files(
    config: CGConfig,
    context: click.Context,
    object_type: str,
    identifier: str,
    dry_run: bool,
):
    """Retrieve all spring files for a given identity"""
    status_api: Store = config.status_db
    housekeeper_api: HousekeeperAPI = config.housekeeper_api

    samples: list[Sample] = _get_samples(status_api, object_type, identifier)

    for sample in samples:
        latest_version: hk_models.Version = housekeeper_api.last_version(bundle=sample.internal_id)
        spring_files: Iterable[hk_models.File] = housekeeper_api.files(
            bundle=sample.internal_id,
            tags=[SequencingFileTag.SPRING],
            version=latest_version.id,
        )
        for spring_file in spring_files:
            context.invoke(retrieve_spring_file, spring_file_path=spring_file.path, dry_run=dry_run)


def _get_samples(status_api: Store, object_type: str, identifier: str) -> list[Sample]:
    """Gets all samples belonging to a sample, case or flow cell id"""
    get_samples = {
        "sample": status_api.sample,
        "case": status_api.get_samples_by_case_id,
        "flow_cell": status_api.get_samples_from_flow_cell,
    }
    samples: Sample | list[Sample] = get_samples[object_type](identifier)
    return samples if isinstance(samples, list) else [samples]


@backup.command("retrieve-spring-file")
@click.argument("spring-file-path", type=click.Path())
@DRY_RUN
@click.pass_obj
def retrieve_spring_file(config: CGConfig, spring_file_path: str, dry_run: bool):
    """Retrieve a spring file from PDC"""
    LOG.info(f"Attempting PDC retrieval and decryption file {spring_file_path}")
    housekeeper_api: HousekeeperAPI = config.housekeeper_api
    pdc_api: PdcAPI = PdcAPI(binary_path=config.pdc.binary_path, dry_run=dry_run)
    encryption_api: SpringEncryptionAPI = SpringEncryptionAPI(
        binary_path=config.encryption.binary_path,
        dry_run=dry_run,
    )
    LOG.debug(f"Start spring retrieval if not dry run mode={dry_run}")
    spring_backup_api: SpringBackupAPI = SpringBackupAPI(
        encryption_api=encryption_api,
        hk_api=housekeeper_api,
        pdc_api=pdc_api,
        dry_run=dry_run,
    )
    spring_backup_api.retrieve_and_decrypt_spring_file(Path(spring_file_path))
