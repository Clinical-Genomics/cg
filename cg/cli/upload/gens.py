"""Module for uploading to Gens via CLI."""
import logging
from typing import Optional

import click
from cg.apps.gens import GensAPI
from cg.apps.housekeeper.hk import HousekeeperAPI
from cg.models.cg_config import CGConfig
from cg.store import Store, models

from cg.cli.upload.utils import suggest_cases_to_upload
from cg.cli.workflow.commands import (
    ARGUMENT_CASE_ID,
    OPTION_DRY,
)

LOG = logging.getLogger(__name__)


@click.command()
@ARGUMENT_CASE_ID
@OPTION_DRY
@click.pass_obj
def gens(context: CGConfig, case_id: Optional[str], dry_run: bool):
    """Upload data from an analysis to Gens."""

    status_db: Store = context.status_db
    housekeeper_api: HousekeeperAPI = context.housekeeper_api
    gens_api: GensAPI = context.gens_api

    click.echo(click.style("----------------- GENS -------------------"))

    if not case_id:
        suggest_cases_to_upload(status_db=status_db)
        raise click.Abort

    family: models.Family = status_db.family(case_id)
    analysis: models.Analysis = family.analyses[0]

    for link in family.links:
        analysis_date = analysis.started_at or analysis.completed_at
        hk_version = housekeeper_api.version(case_id, analysis_date)
        hk_fracsnp = housekeeper_api.files(
            version=hk_version.id, tags=[link.sample.internal_id, "gens", "fracsnp", "bed"]
        ).first()
        hk_coverage = housekeeper_api.files(
            version=hk_version.id, tags=[link.sample.internal_id, "gens", "coverage", "bed"]
        ).first()

        if dry_run:
            LOG.info(f"Dry run. Would upload data for {family.internal_id} to Gens.")
            return

        gens_api.load(
            sample_id=link.sample.internal_id,
            genome_build=analysis.genome_build,
            baf_path=hk_fracsnp.full_path,
            coverage_path=hk_coverage.full_path,
            case_id=case_id,
        )
