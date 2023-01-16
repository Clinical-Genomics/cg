"""Code for uploading to Gens via CLI"""
import logging
from typing import Optional

import click
from cg.apps.gens import GensAPI
from cg.apps.housekeeper.hk import HousekeeperAPI
from cg.models.cg_config import CGConfig
from cg.store import Store, models

from .utils import suggest_cases_to_upload

LOG = logging.getLogger(__name__)


@click.command()
@click.argument("case_id", required=False)
@click.pass_obj
def gens(context: CGConfig, case_id: Optional[str]):
    """Upload data from an analysis to Gens."""

    status_db: Store = context.status_db
    housekeeper_api: HousekeeperAPI = context.housekeeper_api
    gens_api: GensAPI = context.gens_api

    click.echo(click.style("----------------- GENS -------------------"))

    if not case_id:
        suggest_cases_to_upload(status_db=status_db)
        raise click.Abort

    family_obj: models.Family = status_db.family(case_id)
    analysis_obj: models.Analysis = family_obj.analyses[0]

    for link_obj in family_obj.links:
        analysis_date = analysis_obj.started_at or analysis_obj.completed_at
        hk_version = housekeeper_api.version(case_id, analysis_date)
        hk_fracsnp = housekeeper_api.files(
            version=hk_version.id, tags=[link_obj.sample.internal_id, "gens", "fracsnp", "bed"]
        ).first()
        hk_coverage = housekeeper_api.files(
            version=hk_version.id, tags=[link_obj.sample.internal_id, "gens", "coverage", "bed"]
        ).first()
        gens_api.load(
            sample_id=link_obj.sample.internal_id,
            genome_build=analysis_obj.genome_build,
            baf_path=hk_fracsnp.full_path,
            coverage_path=hk_coverage.full_path,
            case_id=case_id,
        )
