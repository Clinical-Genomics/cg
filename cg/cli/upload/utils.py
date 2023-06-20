"""Utility functions for the upload cli commands."""

import logging
from typing import List, Optional

import click
from cg.constants import Pipeline
from cg.constants.constants import MAX_ITEMS_TO_RETRIEVE
from cg.store import Store
from cg.store.models import Analysis, Family

LOG = logging.getLogger(__name__)


def suggest_cases_to_upload(status_db: Store, pipeline: Optional[Pipeline] = None) -> None:
    """Print a list of suggested cases to upload."""
    LOG.warning("Provide a case, suggestions:")
    records: List[Analysis] = status_db.get_analyses_to_upload(pipeline=pipeline)[
        :MAX_ITEMS_TO_RETRIEVE
    ]
    for case_obj in records:
        click.echo(case_obj)


def is_dna_case_uploaded(dna_case: Family) -> bool:
    return dna_case.analyses and dna_case.analyses[0].uploaded_at
