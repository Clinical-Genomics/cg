"""Backup related CLI commands."""
import logging
from pathlib import Path
from typing import Dict, Iterable, List, Optional, Union

import click
import housekeeper.store.models as hk_models

from cg.apps.crunchy.sbatch import FLOW_CELL_ENCRYPT_COMMANDS, FLOW_CELL_ENCRYPT_ERROR
from cg.apps.housekeeper.hk import HousekeeperAPI
from cg.constants import FileExtensions
from cg.constants.constants import DRY_RUN, FlowCellStatus
from cg.constants.housekeeper_tags import SequencingFileTag
from cg.constants.priority import SlurmQos
from cg.exc import FlowCellError
from cg.meta.backup.backup import BackupAPI, SpringBackupAPI
from cg.meta.backup.pdc import PdcAPI
from cg.meta.encryption.encryption import (
    EncryptionAPI,
    FlowCellEncryptionAPI,
    SpringEncryptionAPI,
)
from cg.meta.tar.tar import TarAPI
from cg.models.cg_config import CGConfig
from cg.models.demultiplex.flow_cell import FlowCellDirectoryData
from cg.models.slurm.sbatch import Sbatch
from cg.store import Store
from cg.store.models import Flowcell, Sample

LOG = logging.getLogger(__name__)


@click.group()
@click.pass_obj
def backup(context: CGConfig):
    """Backup utilities"""
    pass


@backup.command("encrypt-flow-cell")
@click.option("-f", "--flow-cell-id", help="Retrieve a specific flow cell, ex. 'HCK2KDSXX'")
@DRY_RUN
@click.pass_obj
def encrypt_flow_cell(context: CGConfig, dry_run: bool, flow_cell_id: Optional[str] = None):
    """Encrypt flow cell."""
    flow_cell_encryption_api = FlowCellEncryptionAPI(binary_path=context.encryption.binary_path, dry_run=dry_run)
    tar_api = TarAPI(binary_path=context.tar.binary_path, dry_run=dry_run)
    encrypt_dir: Dict[str, str] = context.backup.encrypt_dir.dict()
    flow_cells_dir: Path = Path(context.flow_cells_dir)
    LOG.debug(f"Search for flow cells ready to encrypt in {flow_cells_dir}")
    for sub_dir in flow_cells_dir.iterdir():
        if not sub_dir.is_dir():
            continue
        LOG.debug(f"Found directory {sub_dir}")
        try:
            flow_cell = FlowCellDirectoryData(flow_cell_path=sub_dir)
        except FlowCellError:
            continue
        if not flow_cell.is_flow_cell_ready():
            continue
        flow_cell_encrypt_dir: Path = Path(encrypt_dir.get("current"), flow_cell.id)
        flow_cell_encrypt_file_path_prefix: Path = Path(flow_cell_encrypt_dir, flow_cell.id)
        pending_file_path: Path = flow_cell_encrypt_file_path_prefix.with_suffix(".pending")
        if flow_cell_encrypt_dir.exists() and pending_file_path.exists():
            LOG.debug(f"Encryption already started for flow cell: {flow_cell.id}")
            continue
        flow_cell_encrypt_dir.mkdir(exist_ok=True, parents=True)
        sbatch_cores: int = 12
        compressed_flow_cell_gpg_suffix: str = f"{FileExtensions.TAR}{FileExtensions.GZIP}{FileExtensions.GPG}"
        compressed_flow_cell_md5sum_suffix: str = f"{FileExtensions.TAR}{FileExtensions.GZIP}.md5sum"
        compressed_flow_cell_degpg_md5sum_suffix: str = f"{FileExtensions.TAR}{FileExtensions.GZIP}.degpg.md5sum"
        flow_cell_encryption_api.create_pending_file(pending_path=pending_file_path)
        symetric_passphrase_file_path: Path = flow_cell_encrypt_file_path_prefix.with_suffix(".passphrase")
        final_passphrase_suffix: str = f".key{FileExtensions.GPG}"
        error_function = FLOW_CELL_ENCRYPT_ERROR.format(flow_cell_encrypt_dir=flow_cell_encrypt_dir)
        commands = FLOW_CELL_ENCRYPT_COMMANDS(symmetric_passphrase_cmd=flow_cell_encryption_api.get_symmetric_passphrase_cmd(passphrase_file_path=symetric_passphrase_file_path),
                                              asymmetrically_encrypt_passphrase_cmd=flow_cell_encryption_api.get_asymmetrically_encrypt_passphrase_cmd(passphrase_file_path=symetric_passphrase_file_path),
                                              tar_encrypt_flow_cell_dir_cmd=tar_api.get_compress_cmd(input_path=flow_cell_encrypt_dir),
                                              parallel_gzip_cmd=f"pigz p {sbatch_cores} --fast -c",
                                              tee_cmd=f"tee (md5sum > {flow_cell_encrypt_file_path_prefix.with_suffix(compressed_flow_cell_md5sum_suffix)})",
                                              flow_cell_symmetric_encryption_cmd=flow_cell_encryption_api.get_flow_cell_symmetric_encryption_command(output_file=flow_cell_encrypt_file_path_prefix.with_suffix(compressed_flow_cell_gpg_suffix), passphrase_file_path=symetric_passphrase_file_path),
                                              flow_cell_symmetric_decryption_cmd=flow_cell_encryption_api.get_flow_cell_symmetric_decryption_command(input_file=flow_cell_encrypt_file_path_prefix.with_suffix(compressed_flow_cell_gpg_suffix), passphrase_file_path=symetric_passphrase_file_path),
                                              md5sum_cmd=f"md5sum > {flow_cell_encrypt_file_path_prefix.with_suffix(compressed_flow_cell_degpg_md5sum_suffix)}",
                                              diff_cmd=f"diff -q {flow_cell_encrypt_file_path_prefix.with_suffix(compressed_flow_cell_md5sum_suffix)} {flow_cell_encrypt_file_path_prefix.with_suffix(compressed_flow_cell_degpg_md5sum_suffix)}",
                                              mv_passphrase_file_cmd=f"mv {symetric_passphrase_file_path.with_suffix(FileExtensions.GPG)} {flow_cell_encrypt_file_path_prefix.with_suffix(final_passphrase_suffix)}"
                                              )

        sbatch_parameters: Sbatch = Sbatch(
            account="production",
            commands=commands,
            email="a_mail",
            error=error_function,
            hours=24,
            job_name="_".join([flow_cell.id, "flow_cell_encryption"]),
            log_dir="a log dir",
            memory=60,
            number_tasks=sbatch_cores,
            quality_of_service=SlurmQos.HIGH,
        )
        sbatch_content: str = slurm_api.generate_sbatch_content(sbatch_parameters)
        sbatch_path = files.get_spring_to_fastq_sbatch_path(
            log_dir=log_dir, run_name=compression_obj.run_name
        )
        sbatch_number: int = self.slurm_api.submit_sbatch(
            sbatch_content=sbatch_content, sbatch_path=sbatch_path
        )
        LOG.info("Spring decompression running as job %s", sbatch_number)


@backup.command("fetch-flow-cell")
@click.option("-f", "--flow-cell-id", help="Retrieve a specific flow cell, ex. 'HCK2KDSXX'")
@DRY_RUN
@click.pass_obj)
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
        flow_cells_dir=context.flow_cells_dir,
        dry_run=dry_run,
    )
    backup_api: BackupAPI = context.meta_apis["backup_api"]

    status_api: Store = context.status_db
    flow_cell: Optional[Flowcell] = (
        status_api.get_flow_cell_by_name(flow_cell_name=flow_cell_id) if flow_cell_id else None
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

    samples: List[Sample] = _get_samples(status_api, object_type, identifier)

    for sample in samples:
        latest_version: hk_models.Version = housekeeper_api.last_version(bundle=sample.internal_id)
        spring_files: Iterable[hk_models.File] = housekeeper_api.files(
            bundle=sample.internal_id,
            tags=[SequencingFileTag.SPRING],
            version=latest_version.id,
        )
        for spring_file in spring_files:
            context.invoke(retrieve_spring_file, spring_file_path=spring_file.path, dry_run=dry_run)


def _get_samples(status_api: Store, object_type: str, identifier: str) -> List[Sample]:
    """Gets all samples belonging to a sample, case or flow cell id"""
    get_samples = {
        "sample": status_api.sample,
        "case": status_api.get_samples_by_case_id,
        "flow_cell": status_api.get_samples_from_flow_cell,
    }
    samples: Union[Sample, List[Sample]] = get_samples[object_type](identifier)
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
