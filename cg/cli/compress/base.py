"""Commands for compressing files, and cleaning uncompressed files"""

import logging

import click

from cg.cli.compress.fastq import (
    clean_fastq,
    decompress_case,
    decompress_flowcell,
    decompress_sample,
    decompress_ticket,
    fastq_cmd,
    fix_spring,
)
from cg.cli.utils import CLICK_CONTEXT_SETTINGS
from cg.meta.backup.backup import SpringBackupAPI
from cg.meta.backup.pdc import PdcAPI
from cg.meta.compress import CompressAPI
from cg.meta.encryption.encryption import SpringEncryptionAPI
from cg.models.cg_config import CGConfig

LOG = logging.getLogger(__name__)


@click.group(context_settings=CLICK_CONTEXT_SETTINGS)
@click.pass_obj
def compress(context: CGConfig):
    """Compress files"""

    hk_api = context.housekeeper_api
    crunchy_api = context.crunchy_api

    compress_api = CompressAPI(
        hk_api=hk_api,
        crunchy_api=crunchy_api,
        demux_root=context.run_instruments.illumina.demultiplexed_runs_dir,
    )
    context.meta_apis["compress_api"] = compress_api


compress.add_command(fastq_cmd)


@compress.group()
def clean():
    """Clean uncompressed files"""


clean.add_command(clean_fastq)
clean.add_command(fix_spring)


@click.group(context_settings=CLICK_CONTEXT_SETTINGS)
@click.pass_obj
def decompress(context: CGConfig):
    """Decompress files"""
    hk_api = context.housekeeper_api
    crunchy_api = context.crunchy_api

    pdc_api: PdcAPI = PdcAPI(binary_path=context.pdc.binary_path)
    spring_encryption_api: SpringEncryptionAPI = SpringEncryptionAPI(
        binary_path=context.encryption.binary_path,
    )
    spring_backup_api: SpringBackupAPI = SpringBackupAPI(
        encryption_api=spring_encryption_api,
        hk_api=hk_api,
        pdc_api=pdc_api,
    )
    LOG.debug("Start spring retrieval if not dry run")

    compress_api = CompressAPI(
        hk_api=hk_api,
        crunchy_api=crunchy_api,
        demux_root=context.run_instruments.illumina.demultiplexed_runs_dir,
        backup_api=spring_backup_api,
    )

    context.meta_apis["compress_api"] = compress_api
    LOG.info("Running decompress spring")


decompress.add_command(decompress_sample)
decompress.add_command(decompress_case)
decompress.add_command(decompress_ticket)
decompress.add_command(decompress_flowcell)
