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
from cg.constants.constants import SequencingRunDataAvailability
from cg.constants.housekeeper_tags import SequencingFileTag
from cg.exc import (
    DsmcAlreadyRunningError,
    FlowCellError,
    IlluminaRunAlreadyBackedUpError,
    IlluminaRunEncryptionError,
    PdcError,
)
from cg.meta.backup.backup import SpringBackupAPI
from cg.meta.encryption.encryption import EncryptionAPI, SpringEncryptionAPI
from cg.meta.tar.tar import TarAPI
from cg.models.cg_config import CGConfig
from cg.models.run_devices.illumina_run_directory_data import (
    IlluminaRunDirectoryData,
    get_sequencing_runs_from_path,
)
from cg.services.illumina.backup.backup_service import IlluminaBackupService
from cg.services.illumina.backup.encrypt_service import (
    IlluminaRunEncryptionService,
)
from cg.services.pdc_service.pdc_service import PdcService
from cg.store.exc import EntryNotFoundError
from cg.store.models import IlluminaSequencingRun, Sample
from cg.store.store import Store

LOG = logging.getLogger(__name__)


@click.group(context_settings=CLICK_CONTEXT_SETTINGS)
@click.pass_obj
def backup(context: CGConfig):
    """Backup utilities"""
    pass


@backup.command("illumina-runs")
@DRY_RUN
@click.pass_obj
def backup_illumina_runs(context: CGConfig, dry_run: bool):
    """Back-up Illumina runs."""
    pdc_service = context.pdc_service
    pdc_service.dry_run = dry_run
    encryption_api = EncryptionAPI(binary_path=context.encryption.binary_path, dry_run=dry_run)
    tar_api = TarAPI(binary_path=context.tar.binary_path, dry_run=dry_run)
    backup_service = IlluminaBackupService(
        encryption_api=encryption_api,
        pdc_archiving_directory=context.illumina_backup_service.pdc_archiving_directory,
        status_db=context.status_db,
        tar_api=tar_api,
        pdc_service=pdc_service,
        sequencing_runs_dir=context.run_instruments.illumina.sequencing_runs_dir,
        dry_run=dry_run,
    )
    backup_service.dry_run = dry_run
    status_db: Store = context.status_db
    runs_dir_data: list[IlluminaRunDirectoryData] = get_sequencing_runs_from_path(
        sequencing_run_dir=Path(context.run_instruments.illumina.sequencing_runs_dir)
    )
    for run_dir_data in runs_dir_data:
        try:
            sequencing_run: IlluminaSequencingRun = (
                status_db.get_illumina_sequencing_run_by_device_internal_id(run_dir_data.id)
            )
            backup_service.start_run_backup(
                run_dir_data=run_dir_data,
                sequencing_run=sequencing_run,
                status_db=status_db,
                binary_path=context.encryption.binary_path,
                encryption_dir=Path(context.encryption.encryption_dir),
                pigz_binary_path=context.pigz.binary_path,
                sbatch_parameter=context.illumina_backup_service.slurm_flow_cell_encryption.dict(),
            )
        except EntryNotFoundError as error:
            logging.error(f"{error}")
            continue
        except (
            DsmcAlreadyRunningError,
            IlluminaRunAlreadyBackedUpError,
            IlluminaRunEncryptionError,
            PdcError,
        ) as error:
            logging.error(f"{error}")


@backup.command("encrypt-illumina-runs")
@DRY_RUN
@click.pass_obj
def encrypt_illumina_runs(context: CGConfig, dry_run: bool):
    """Encrypt illumina runs."""
    status_db: Store = context.status_db
    runs: list[IlluminaRunDirectoryData] = get_sequencing_runs_from_path(
        sequencing_run_dir=Path(context.run_instruments.illumina.sequencing_runs_dir)
    )
    for run in runs:
        try:
            sequencing_run: IlluminaSequencingRun = (
                status_db.get_illumina_sequencing_run_by_device_internal_id(run.id)
            )
        except EntryNotFoundError as error:
            LOG.error(f"{error}")
            continue
        if sequencing_run.has_backup:
            LOG.debug(f"Run: {run.id} is already backed-up")
            continue
        illumina_run_encryption_service = IlluminaRunEncryptionService(
            binary_path=context.encryption.binary_path,
            dry_run=dry_run,
            encryption_dir=Path(context.encryption.encryption_dir),
            run_dir_data=run,
            pigz_binary_path=context.pigz.binary_path,
            slurm_api=SlurmAPI(),
            sbatch_parameter=context.illumina_backup_service.slurm_flow_cell_encryption.dict(),
            tar_api=TarAPI(binary_path=context.tar.binary_path, dry_run=dry_run),
        )
        try:
            illumina_run_encryption_service.start_encryption()
        except (FlowCellError, IlluminaRunEncryptionError) as error:
            logging.error(f"{error}")


@backup.command("fetch-illumina-run")
@click.option("-f", "--flow-cell-id", help="Retrieve a specific flow cell, ex. 'HCK2KDSXX'")
@DRY_RUN
@click.pass_obj
def fetch_illumina_run(context: CGConfig, dry_run: bool, flow_cell_id: str | None = None):
    """Fetch the first Illumina run in the requested queue from backup."""

    pdc_service = context.pdc_service
    pdc_service.dry_run = dry_run
    encryption_api = EncryptionAPI(binary_path=context.encryption.binary_path, dry_run=dry_run)
    tar_api = TarAPI(binary_path=context.tar.binary_path, dry_run=dry_run)
    context.meta_apis["backup_api"] = IlluminaBackupService(
        encryption_api=encryption_api,
        pdc_archiving_directory=context.illumina_backup_service.pdc_archiving_directory,
        status_db=context.status_db,
        tar_api=tar_api,
        pdc_service=pdc_service,
        sequencing_runs_dir=context.run_instruments.illumina.sequencing_runs_dir,
        dry_run=dry_run,
    )
    backup_api: IlluminaBackupService = context.meta_apis["backup_api"]

    status_db: Store = context.status_db
    sequencing_run: IlluminaSequencingRun | None = None
    if not flow_cell_id:
        LOG.info("Fetching first sequencing run in queue")
    try:
        if flow_cell_id:
            sequencing_run: IlluminaSequencingRun = (
                status_db.get_illumina_sequencing_run_by_device_internal_id(flow_cell_id)
            )
    except EntryNotFoundError as error:
        LOG.error(f"{error}")
        raise click.Abort

    retrieval_time: float | None = backup_api.fetch_sequencing_run(sequencing_run)

    if retrieval_time:
        hours = retrieval_time / 60 / 60
        LOG.info(f"Retrieval time: {hours:.1}h")
        return

    if not dry_run and sequencing_run:
        LOG.info(
            f"{sequencing_run}: updating sequencing run data availability to {SequencingRunDataAvailability.REQUESTED}"
        )
        status_db.update_illumina_sequencing_run_data_availability(
            sequencing_run=sequencing_run, data_availability=SequencingRunDataAvailability.REQUESTED
        )


@backup.command("archive-spring-files")
@DRY_RUN
@click.pass_context
@click.pass_obj
def archive_spring_files(config: CGConfig, context: click.Context, dry_run: bool):
    """Archive spring files to PDC."""
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
    """Archive a spring file to PDC."""
    housekeeper_api: HousekeeperAPI = config.housekeeper_api
    pdc_service: PdcService = PdcService(binary_path=config.pdc.binary_path, dry_run=dry_run)
    encryption_api: SpringEncryptionAPI = SpringEncryptionAPI(
        binary_path=config.encryption.binary_path,
        dry_run=dry_run,
    )
    spring_backup_api: SpringBackupAPI = SpringBackupAPI(
        encryption_api=encryption_api,
        hk_api=housekeeper_api,
        pdc_service=pdc_service,
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
    """Retrieve all spring files for a given identity."""
    status_api: Store = config.status_db
    housekeeper_api: HousekeeperAPI = config.housekeeper_api

    samples: list[Sample] = status_api.get_samples_by_identifier(
        object_type=object_type, identifier=identifier
    )

    for sample in samples:
        latest_version: hk_models.Version = housekeeper_api.last_version(bundle=sample.internal_id)
        spring_files: Iterable[hk_models.File] = housekeeper_api.files(
            bundle=sample.internal_id,
            tags=[SequencingFileTag.SPRING],
            version=latest_version.id,
        )
        for spring_file in spring_files:
            context.invoke(retrieve_spring_file, spring_file_path=spring_file.path, dry_run=dry_run)


@backup.command("retrieve-spring-file")
@click.argument("spring-file-path", type=click.Path())
@DRY_RUN
@click.pass_obj
def retrieve_spring_file(config: CGConfig, spring_file_path: str, dry_run: bool):
    """Retrieve a spring file from PDC."""
    LOG.info(f"Attempting PDC retrieval and decryption file {spring_file_path}")
    housekeeper_api: HousekeeperAPI = config.housekeeper_api
    pdc_service: PdcService = PdcService(binary_path=config.pdc.binary_path, dry_run=dry_run)
    encryption_api: SpringEncryptionAPI = SpringEncryptionAPI(
        binary_path=config.encryption.binary_path,
        dry_run=dry_run,
    )
    LOG.debug(f"Start spring retrieval if not dry run mode={dry_run}")
    spring_backup_api: SpringBackupAPI = SpringBackupAPI(
        encryption_api=encryption_api,
        hk_api=housekeeper_api,
        pdc_service=pdc_service,
        dry_run=dry_run,
    )
    spring_backup_api.retrieve_and_decrypt_spring_file(Path(spring_file_path))
