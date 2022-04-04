"""Backup related CLI commands"""
import logging
from pathlib import Path
from typing import Optional

import alchy.query
import click
import housekeeper.store.models

from cg.apps.housekeeper.hk import HousekeeperAPI
from cg.constants.constants import DRY_RUN, HousekeeperTags
from cg.meta.backup.backup import BackupApi, SpringBackupAPI
from cg.meta.backup.pdc import PdcAPI
from cg.meta.encryption.encryption import SpringEncryptionAPI
from cg.models.cg_config import CGConfig
from cg.store import Store, models

LOG = logging.getLogger(__name__)


@click.group()
@click.pass_obj
def backup(context: CGConfig):
    """Backup utilities."""
    pdc_api = PdcAPI()
    context.meta_apis["backup_api"] = BackupApi(
        status=context.status_db,
        pdc_api=pdc_api,
        root_dir=context.backup.root.dict(),
    )


@backup.command("fetch-flowcell")
@click.option("-f", "--flowcell", help="Retrieve a specific flow cell")
@click.option("--dry-run", is_flag=True, help="Don't retrieve from PDC or set flow cell status")
@click.pass_obj
def fetch_flowcell(context: CGConfig, dry_run: bool, flowcell: str):
    """Fetch the first flow cell in the requested queue from backup."""
    status_api: Store = context.status_db
    backup_api: BackupApi = context.meta_apis["backup_api"]

    flowcell_obj: Optional[models.Flowcell] = None
    if flowcell:
        flowcell_obj: Optional[models.Flowcell] = status_api.flowcell(flowcell)
        if flowcell_obj is None:
            LOG.error(f"{flowcell}: not found in database")
            raise click.Abort

    retrieval_time: Optional[float] = backup_api.fetch_flowcell(
        flowcell_obj=flowcell_obj, dry_run=dry_run
    )

    if retrieval_time:
        hours = retrieval_time / 60 / 60
        LOG.info(f"Retrieval time: {hours:.1}h")
        return

    if not flowcell:
        return

    if not dry_run:
        LOG.info(f"{flowcell}: updating flow cell status to requested")
        flowcell_obj.status = "requested"
        status_api.commit()


@backup.command("archive-spring-files")
@DRY_RUN
@click.pass_context
@click.pass_obj
def archive_spring_files(config: CGConfig, context: click.Context, dry_run: bool):
    """Archive spring files to PDC"""
    housekeeper_api: HousekeeperAPI = config.housekeeper_api
    LOG.info("Getting all spring files from Housekeeper.")
    all_spring_files: alchy.query.Query = housekeeper_api.files(
        tags=[HousekeeperTags.SPRING]
    ).filter(housekeeper.store.models.File.path.like(f"%{config.environment}%"))
    for spring_file in all_spring_files:
        try:
            LOG.info("Attempting encryption and PDC archiving for file %s", spring_file.path)
            context.invoke(archive_spring_file, spring_file_path=spring_file.path, dry_run=dry_run)
        except FileNotFoundError:
            LOG.warning(
                "Spring file %s found in Housekeeper, but not on Hasta! Skipping encryption!",
                spring_file.path,
            )
            continue


@backup.command("archive-spring-file")
@DRY_RUN
@click.pass_obj
def archive_spring_file(config: CGConfig, spring_file_path: str, dry_run: bool):
    """Archive a spring file to PDC"""
    housekeeper_api: HousekeeperAPI = config.housekeeper_api
    pdc_api: PdcAPI = PdcAPI(binary_path=config.pdc.binary_path)
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
    LOG.debug("Start spring encryption/backup here")
    spring_backup_api.encrypt_and_archive_spring_file(Path(spring_file_path))


@backup.command("retrieve-spring-file")
@DRY_RUN
@click.pass_obj
def retrieve_spring_file(config: CGConfig, spring_file_path: str, dry_run: bool):
    """Retrieve a spring file from PDC"""
    housekeeper_api: HousekeeperAPI = config.housekeeper_api
    pdc_api: PdcAPI = PdcAPI(binary_path=config.pdc.binary_path)
    encryption_api: SpringEncryptionAPI = SpringEncryptionAPI(
        binary_path=config.encryption.binary_path,
        dry_run=dry_run,
    )
    LOG.debug("Start spring retrieval if not dry run")
    spring_backup_api: SpringBackupAPI = SpringBackupAPI(
        encryption_api=encryption_api,
        hk_api=housekeeper_api,
        pdc_api=pdc_api,
        dry_run=dry_run,
    )
    spring_backup_api.retrieve_and_decrypt_spring_file(Path(spring_file_path))


@backup.command("retrieve-spring-files-sample")
@DRY_RUN
@click.argument("sample-id", type=str)
@click.pass_context
@click.pass_obj
def retrieve_spring_files_for_sample(
    config: CGConfig, context: click.Context, sample_id: str, dry_run: bool
):
    """Retrieve all spring files for a given sample"""
    housekeeper_api: HousekeeperAPI = config.housekeeper_api
    latest_version = housekeeper_api.last_version(bundle=sample_id)

    spring_files = housekeeper_api.files(
        bundle=sample_id, tags=["spring"], version=latest_version.id
    )
    for spring_file in spring_files:
        try:
            LOG.info("Attempting PDC retrieval and decryption file %s", spring_file.path)
            context.invoke(retrieve_spring_file, spring_file_path=spring_file.path, dry_run=dry_run)
        except FileNotFoundError:
            LOG.warning(
                "Spring file %s found in Housekeeper, but not on Hasta! Skipping encryption!",
                spring_file.path,
            )
            continue


@backup.command("retrieve-spring-files-case")
@DRY_RUN
@click.argument("case-id", type=str)
@click.pass_context
@click.pass_obj
def retrieve_spring_files_for_case(
    config: CGConfig, context: click.Context, case_id: str, dry_run: bool
):
    """Retrieve all spring files for a given case"""
    breakpoint()
    status_api: Store = config.status_db
    housekeeper_api: HousekeeperAPI = config.housekeeper_api

    case_obj = status_api.family(case_id)
    sample_ids = [link.sample.internal_id for link in case_obj.links]

    for sample_id in sample_ids:
        latest_version = housekeeper_api.last_version(bundle=sample_id)
        spring_files = housekeeper_api.files(
            bundle=sample_id, tags=["spring"], version=latest_version.id
        )
        for spring_file in spring_files:
            try:
                LOG.info("Attempting PDC retrieval and decryption file %s", spring_file.path)
                context.invoke(
                    retrieve_spring_file, spring_file_path=spring_file.path, dry_run=dry_run
                )
            except FileNotFoundError:
                LOG.warning(
                    "Spring file %s found in Housekeeper, but not on Hasta! Skipping encryption!",
                    spring_file.path,
                )
                continue


@backup.command("retrieve-spring-files-flow-cell")
@DRY_RUN
@click.argument("flow-cell-id", type=str)
@click.pass_context
@click.pass_obj
def retrieve_spring_files_for_flow_cell(
    config: CGConfig, context: click.Context, flow_cell_id: str, dry_run: bool
):
    """Retrieve all spring files for a given flow cell"""

    status_api: Store = config.status_db
    housekeeper_api: HousekeeperAPI = config.housekeeper_api

    sample_objs = status_api.get_samples_from_flowcell(flow_cell_id)
    sample_ids = [sample.internal_id for sample in sample_objs]

    for sample_id in sample_ids:
        latest_version = housekeeper_api.last_version(bundle=sample_id)
        spring_files = housekeeper_api.files(
            bundle=sample_id, tags=["spring"], version=latest_version.id
        )
        for spring_file in spring_files:
            try:
                LOG.info("Attempting PDC retrieval and decryption file %s", spring_file.path)
                context.invoke(
                    retrieve_spring_file, spring_file_path=spring_file.path, dry_run=dry_run
                )
            except FileNotFoundError:
                LOG.warning(
                    "Spring file %s found in Housekeeper, but not on Hasta! Skipping encryption!",
                    spring_file.path,
                )
                continue
