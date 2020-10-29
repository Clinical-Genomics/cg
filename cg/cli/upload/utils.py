"""Utility functions for the upload cli commands"""
import logging
from typing import List

import click

from cg.store import models

LOG = logging.getLogger(__name__)


class LinkHelper:
    """Class that helps handle links"""

    @staticmethod
    def all_samples_are_non_tumour(links: List[models.FamilySample]) -> bool:
        """Return True if all samples are non tumour."""
        return all(not link.sample.is_tumour for link in links)

    @staticmethod
    def get_analysis_type_for_each_link(links: List[models.FamilySample]) -> list:
        """Return analysis type for each sample given by link list"""
        return [link.sample.application_version.application.analysis_type for link in links]


def suggest_cases_to_upload(context):
    LOG.warning("provide a case, suggestions:")
    records = context.obj["status_db"].analyses_to_upload()[:50]
    for family_obj in records:
        click.echo(family_obj)


def suggest_cases_delivery_report(context):
    LOG.error("provide a case, suggestions:")
    records = context.obj["status_db"].analyses_to_delivery_report()[:50]
    for family_obj in records:
        click.echo(family_obj)
