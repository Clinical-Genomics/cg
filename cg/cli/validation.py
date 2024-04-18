"""cg module for validation ofcases."""

import logging
from pathlib import Path
from typing import Tuple

import click

from cg.constants.constants import DRY_RUN
from cg.meta.create_validation_cases.validation_cases_api import CreateValidationCaseAPI
from cg.models.cg_config import CGConfig

LOG = logging.getLogger(__name__)


@click.group()
def validation():
    """Validate workflows."""


@validation.command("create-validation-case")
@click.option(
    "-c",
    "--case-id",
    required=True,
    help="Case identifier used in statusdb, e.g. supersonicturtle. The case information wil be transferred to the validation case.",
)
@click.option(
    "-cn",
    "--case-name",
    required=True,
    help="Case name that is used as name for the validation case.",
)
@click.option(
    "-dv",
    "--delivery",
    required=False,
    help="Delivery option for the validation case, if not set will take delivery option from original case.",
)
@click.option(
    "-da",
    "--data-analysis",
    required=False,
    help="Data analysis option for the validation case, if not set will take data analysis option from original case.",
)
@DRY_RUN
@click.pass_obj
def create_validation_case(
    context: CGConfig, case_id: str, case_name: str, delivery: str, data_analysis: str
):
    """Create a validation case to be used in workflow validation."""
    validation_case_api = CreateValidationCaseAPI(
        status_db=context.status_db, housekeeper_api=context.housekeeper_api
    )

    try:
        validation_case_api.create_validation_case(
            case_id=case_id, case_name=case_name, delivery=delivery, data_analysis=data_analysis
        )
    except Exception as error:
        LOG.error(f"An error occured {repr(error)}.")
        raise click.Abort
