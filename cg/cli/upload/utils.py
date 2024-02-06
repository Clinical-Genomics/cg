"""Utility functions for the upload cli commands."""

import logging

import click

from cg.constants import Workflow
from cg.constants.constants import MAX_ITEMS_TO_RETRIEVE
from cg.store.models import Analysis
from cg.store.store import Store

LOG = logging.getLogger(__name__)


def suggest_cases_to_upload(status_db: Store, workflow: Workflow | None = None) -> None:
    """Print a list of suggested cases to upload."""
    LOG.warning("Provide a case, suggestions:")
    records: list[Analysis] = status_db.get_analyses_to_upload(workflow=workflow)[
        :MAX_ITEMS_TO_RETRIEVE
    ]
    for case_obj in records:
        click.echo(case_obj)
