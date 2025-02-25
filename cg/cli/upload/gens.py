"""Module for uploading to Gens via CLI."""

import logging

import rich_click as click
from housekeeper.store.models import File

from cg.apps.gens import GensAPI
from cg.apps.housekeeper.hk import HousekeeperAPI
from cg.cli.upload.utils import suggest_cases_to_upload
from cg.cli.workflow.commands import ARGUMENT_CASE_ID
from cg.constants.cli_options import DRY_RUN
from cg.constants.gene_panel import GENOME_BUILD_37
from cg.constants.housekeeper_tags import GensAnalysisTag
from cg.models.cg_config import CGConfig
from cg.store.models import Case
from cg.store.store import Store

LOG = logging.getLogger(__name__)


@click.command("gens")
@ARGUMENT_CASE_ID
@DRY_RUN
@click.pass_obj
def upload_to_gens(context: CGConfig, case_id: str | None, dry_run: bool):
    """Upload data from an analysis to Gens."""

    click.echo(click.style("----------------- GENS -------------------"))

    status_db: Store = context.status_db
    housekeeper_api: HousekeeperAPI = context.housekeeper_api
    gens_api: GensAPI = context.gens_api

    gens_api.set_dry_run(dry_run=dry_run)

    if not case_id:
        suggest_cases_to_upload(status_db=status_db)
        raise click.Abort

    family: Case = status_db.get_case_by_internal_id(internal_id=case_id)

    for sample in family.samples:
        hk_coverage: File = housekeeper_api.get_file_from_latest_version(
            bundle_name=case_id, tags=[sample.internal_id] + GensAnalysisTag.COVERAGE
        )
        hk_fracsnp: File = housekeeper_api.get_file_from_latest_version(
            bundle_name=case_id, tags=[sample.internal_id] + GensAnalysisTag.FRACSNP
        )

        if hk_fracsnp and hk_coverage:
            gens_api.load(
                baf_path=hk_fracsnp.full_path,
                case_id=case_id,
                coverage_path=hk_coverage.full_path,
                genome_build=GENOME_BUILD_37,
                sample_id=sample.internal_id,
            )
