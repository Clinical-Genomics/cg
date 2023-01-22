"""Backup related CLI commands."""
import logging
from pathlib import Path
from typing import Iterable, List, Optional, Union

import click
import housekeeper.store.models as hk_models

from cg.apps.housekeeper.hk import HousekeeperAPI
from cg.constants.constants import DRY_RUN, FlowCellStatus
from cg.constants.housekeeper_tags import SequencingFileTag
from cg.meta.backup.backup import BackupAPI, SpringBackupAPI
from cg.meta.backup.pdc import PdcAPI
from cg.meta.encryption.encryption import EncryptionAPI, SpringEncryptionAPI
from cg.meta.tar.tar import TarAPI
from cg.models.cg_config import CGConfig
from cg.store import Store, models

LOG = logging.getLogger(__name__)


@click.group()
@click.pass_obj
def backup(context: CGConfig):
    """Backup utilities"""
    pass


@backup.command("fetch-flow-cell")
@click.option("-f", "--flow-cell-id", help="Retrieve a specific flow cell, ex. 'HCK2KDSXX'")
@DRY_RUN
@click.pass_obj
def fetch_flow_cell(context: CGConfig, dry_run: bool, flow_cell_id: Optional[str] = None):
    """Fetch the first flow cell in the requested queue from backup"""

    pdc_api = PdcAPI(binary_path=context.pdc.binary_path, dry_run=dry_run)
    encryption_api = EncryptionAPI(binary_path=context.encryption.binary_path, dry_run=dry_run)
    tar_api = TarAPI(binary_path=context.tar.binary_path, dry_run=dry_run)
    context.meta_apis["backup_api"] = BackupAPI(
        encryption_api=encryption_api,
        encrypt_dir=context.backup.encrypt_dir.dict(),
        status=context.status_db,
        tar_api=tar_api,
        pdc_api=pdc_api,
        root_dir=context.backup.root.dict(),
        dry_run=dry_run,
    )
    backup_api: BackupAPI = context.meta_apis["backup_api"]

    status_api: Store = context.status_db
    flow_cell: Optional[models.Flowcell] = (
        status_api.get_flow_cell(flow_cell_id=flow_cell_id) if flow_cell_id else None
    )

    if not flow_cell and flow_cell_id:
        LOG.error(f"{flow_cell_id}: not found in database")
        raise click.Abort

    if not flow_cell_id:
        LOG.info("Fetching first flow cell in queue")

    retrieval_time: Optional[float] = backup_api.fetch_flow_cell(flow_cell=flow_cell)

    if retrieval_time:
        hours = retrieval_time / 60 / 60
        LOG.info(f"Retrieval time: {hours:.1}h")
        return

    if not dry_run and flow_cell:
        LOG.info(f"{flow_cell}: updating flow cell status to {FlowCellStatus.REQUESTED}")
        flow_cell.status = FlowCellStatus.REQUESTED
        status_api.commit()


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
    ).filter(hk_models.File.path.like(f"%{config.environment}/{config.demultiplex.out_dir}%"))
    for spring_file in spring_files:
        LOG.info("Attempting encryption and PDC archiving for file %s", spring_file.path)
        if Path(spring_file.path).exists():
            context.invoke(archive_spring_file, spring_file_path=spring_file.path, dry_run=dry_run)
        else:
            LOG.warning(
                "Spring file %s found in Housekeeper, but not on disk! Archiving process skipped!",
                spring_file.path,
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
@click.option("-f", "--flow-cell-id", "object_type", flag_value="flow_cell", type=str)
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

    samples: List[models.Sample] = _get_samples(status_api, object_type, identifier)

    for sample in samples:
        latest_version: hk_models.Version = housekeeper_api.last_version(bundle=sample.internal_id)
        spring_files: Iterable[hk_models.File] = housekeeper_api.files(
            bundle=sample.internal_id,
            tags=[SequencingFileTag.SPRING],
            version=latest_version.id,
        )
        for spring_file in spring_files:
            context.invoke(retrieve_spring_file, spring_file_path=spring_file.path, dry_run=dry_run)


def _get_samples(status_api: Store, object_type: str, identifier: str) -> List[models.Sample]:
    """Gets all samples belonging to a sample, case or flow cell id"""
    get_samples = {
        "sample": status_api.sample,
        "case": status_api.get_samples_by_family_id,
        "flow_cell": status_api.get_samples_from_flowcell,
    }
    samples: Union[models.Sample, List[models.Sample]] = get_samples[object_type](identifier)
    return samples if isinstance(samples, list) else [samples]


@backup.command("retrieve-spring-file")
@click.argument("spring-file-path", type=click.Path())
@DRY_RUN
@click.pass_obj
def retrieve_spring_file(config: CGConfig, spring_file_path: str, dry_run: bool):
    """Retrieve a spring file from PDC"""
    LOG.info("Attempting PDC retrieval and decryption file %s", spring_file_path)
    housekeeper_api: HousekeeperAPI = config.housekeeper_api
    pdc_api: PdcAPI = PdcAPI(binary_path=config.pdc.binary_path, dry_run=dry_run)
    encryption_api: SpringEncryptionAPI = SpringEncryptionAPI(
        binary_path=config.encryption.binary_path,
        dry_run=dry_run,
    )
    LOG.debug("Start spring retrieval if not dry run mode=%s", dry_run)
    spring_backup_api: SpringBackupAPI = SpringBackupAPI(
        encryption_api=encryption_api,
        hk_api=housekeeper_api,
        pdc_api=pdc_api,
        dry_run=dry_run,
    )
    spring_backup_api.retrieve_and_decrypt_spring_file(Path(spring_file_path))
