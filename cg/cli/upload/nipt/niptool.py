import logging
from pathlib import Path

import click

from cg.meta.upload.nipt import NiptUploadAPI
from cg.models.cg_config import CGConfig

LOG = logging.getLogger(__name__)


@click.group()
def niptool():
    """Upload NIPT result files"""
    pass


@niptool.command("case")
@click.argument("case_id", required=True)
@click.option("--dry-run", is_flag=True)
@click.pass_context
def batch(context: CGConfig, case_id: str, dry_run: bool):
    """Loading batch into the NIPT database"""

    LOG.info("*** NIPTool UPLOAD START ***")

    nipt_upload_api = NiptUploadAPI(context)

    nipt_upload_api.upload_to_niptool_database(
        results_file="/Users/maya.brandi/opt/lovedkitten2/2021-02-09/summary.csv",
        multiqc_file="/Users/maya.brandi/opt/lovedkitten2/2021-02-09/multiqc_report.html",
        segmental_calls_file="/Users/maya.brandi/opt/lovedkitten2/2021-02-09/22c-2021-00355-05.WCXpredict_aberrations.filt.bed",
    )


"""   try:
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
            segmental_calls_file=segmental_calls_file,
        )

    except Exception as error:
        LOG.error(f"{error}")
"""
