"""Utility functions for the upload cli commands."""

import logging

import click

from cg.constants import Pipeline
from cg.constants.constants import MAX_ITEMS_TO_RETRIEVE
from cg.store import Store
from cg.store.models import Analysis

LOG = logging.getLogger(__name__)


def suggest_cases_to_upload(status_db: Store, pipeline: Pipeline | None = None) -> None:
    """Print a list of suggested cases to upload."""
    LOG.warning("Provide a case, suggestions:")
    records: list[Analysis] = status_db.get_analyses_to_upload(pipeline=pipeline)[
        :MAX_ITEMS_TO_RETRIEVE
    ]
    for case_obj in records:
        click.echo(case_obj)
