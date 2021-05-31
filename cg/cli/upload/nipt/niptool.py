import logging
from pathlib import Path

import click

from cg.meta.upload.nipt.nipt import NiptUploadAPI
from cg.models.cg_config import CGConfig

LOG = logging.getLogger(__name__)


@click.group()
def niptool():
    """Upload NIPT result files"""
    pass


@niptool.command("case")
@click.argument("case_id", required=True)
@click.option("--dry-run", is_flag=True)
@click.pass_obj
def batch(configs: CGConfig, case_id: str, dry_run: bool):
    """Loading batch into the NIPT database"""

    LOG.info("*** Statina UPLOAD START ***")

    nipt_upload_api = NiptUploadAPI(configs)

    try:
        hk_results_file: str = nipt_upload_api.get_housekeeper_results_file(
            case_id=case_id, tags=["nipt", "metrics"]
        )
        results_file: Path = nipt_upload_api.get_results_file_path(hk_results_file)

        hk_multiqc_file: str = nipt_upload_api.get_housekeeper_results_file(
            case_id=case_id, tags=["nipt", "multiqc-html"]
        )
        multiqc_file: Path = nipt_upload_api.get_results_file_path(hk_multiqc_file)

        hk_segmental_calls_file: str = nipt_upload_api.get_housekeeper_results_file(
            case_id=case_id, tags=["nipt", "wisecondor"]
        )
        segmental_calls_file: Path = nipt_upload_api.get_results_file_path(hk_segmental_calls_file)

        nipt_upload_api.upload_to_niptool_database(
            results_file=results_file,
            multiqc_file=multiqc_file,
            segmental_calls_file=segmental_calls_file.parent,
        )
    except Exception as error:
        LOG.error(f"{error}")
