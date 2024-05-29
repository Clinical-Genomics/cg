import logging

import click


from cg.models.cg_config import CGConfig
from cg.services.create_validation_cases.validation_cases_service import CreateValidationCaseService
from cg.services.validate_file_transfer_service.validate_pacbio_file_transfer_service import (
    ValidatePacbioFileTransferService,
)
from cg.constants.constants import DRY_RUN

LOG = logging.getLogger(__name__)


@click.group()
def validate():
    """Validation of processes in cg."""


@validate.command("pacbio-transfer")
@click.pass_obj
def validate_pacbio_transfer(context: CGConfig):
    """Validate that the PacBio transfer is correct."""
    validate_service = ValidatePacbioFileTransferService(config=context)
    validate_service.validate_all_transfer_done()


@validate.command("create-validation-case")
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
    context: CGConfig,
    case_id: str,
    case_name: str,
    delivery: str,
    data_analysis: str,
    dry_run: bool,
):
    """Create a validation case to be used in workflow validation."""
    validation_case_api = CreateValidationCaseService(
        status_db=context.status_db, housekeeper_api=context.housekeeper_api
    )

    try:
        validation_case_api.create_validation_case(
            case_id=case_id,
            case_name=case_name,
            delivery=delivery,
            data_analysis=data_analysis,
            dry_run=dry_run,
        )
    except Exception as error:
        LOG.error(f"An error occured {repr(error)}.")
        raise click.Abort
