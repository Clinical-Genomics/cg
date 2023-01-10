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
    case_obj: models.Family = status_db.family(case_id)
    
