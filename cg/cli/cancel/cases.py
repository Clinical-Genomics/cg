import logging

import rich_click as click

from cg.apps.environ import get_environ_user
from cg.exc import CgError
from cg.models.cg_config import CGConfig
from cg.services import cancellation_service
from cg.store.store import Store

LOG = logging.getLogger(__name__)


@click.command("cases")
@click.option("--comment", "-m", required=True, help="Reason for cancelling the cases.")
@click.argument("case_ids", nargs=-1, required=True)
@click.pass_obj
def cases(cg_config: CGConfig, comment: str, case_ids: tuple[str, ...]):
    """
    Cancel one or more cases, given by CASE_ID.

    \b
    Following actions are performed:
        - Set the case value `is_cancelled` to true [X]
        - Set the CaseSample links to no-delivery [X]
        - Blocks case from being analyzed
    """  # TODO: remove the check marks
    # TODO: Should I switch to set cancelled_at instead of is_cancelled?
    if not comment.strip():
        raise click.BadParameter(
            "Please add a reason for the cancellation.", param_hint="--comment"
        )
    unique_case_ids: set[str] = set(case_ids)
    status_db: Store = cg_config.status_db

    try:
        cancellation_service.cases(
            case_ids=unique_case_ids, comment=comment, user=get_environ_user(), status_db=status_db
        )
        status_db.commit_to_store()
        click.secho(
            message=f"Cancellation successfully performed for: {', '.join(sorted(unique_case_ids))}",
            fg="green",
        )
    except CgError as error:
        status_db.rollback()
        LOG.error(f"Cancellation failed: {error}. No changes were made.")
        raise click.Abort
    except Exception:
        status_db.rollback()
        LOG.error("Unexpected error during cancellation. No changes were made.")
        raise
