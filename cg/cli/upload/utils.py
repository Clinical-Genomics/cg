"""Utility functions for the upload cli commands."""

import logging
from pathlib import Path
from typing import Optional

import click

from cg.constants import Pipeline
from cg.constants.constants import MAX_ITEMS_TO_RETRIEVE
from cg.store import Store
from cg.store.models import Family

LOG = logging.getLogger(__name__)


def suggest_cases_to_upload(status_db: Store, pipeline: Optional[Pipeline] = None) -> None:
    """Print a list of suggested cases to upload."""
    LOG.warning("Provide a case, suggestions:")
    records = status_db.analyses_to_upload(pipeline=pipeline)[:MAX_ITEMS_TO_RETRIEVE]
    for case_obj in records:
        click.echo(case_obj)


def get_analysis_root_dir(case_obj: Family, context):
    if Pipeline.BALSAMIC in case_obj.data_analysis:
        return Path(context.balsamic.root)
    if Pipeline.MIP_DNA in case_obj.data_analysis:
        return Path(context.mip_rd_dna.root)
    if Pipeline.RNAFUSION in case_obj.data_analysis:
        return Path(context.rnafusion.root)
    else:
        raise ValueError(
            f"Pipeline must be BALSAMIC, MIP and RNAFUSION, but given: {case_obj.data_analysis}."
        )
