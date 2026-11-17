import logging

import rich_click as click

from cg.exc import CgError, CommentMissingError
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
        - Set the case value `is_canceled` to true
        - Set the CaseSample links to no-delivery
        - Blocks linked analyses from being analyzed
        - Blocks reorders of case
    """
    if not comment or not comment.strip():
        # TODO: it could be better to use - raise click.BadParameter("Please add a reason for the cancellation.", param_hint="--comment")
        raise CommentMissingError(f"Please add a reason for the cancellation. User {comment=}")

    status_db: Store = cg_config.status_db
    try:
        cancellation_service.cases(case_ids=list(case_ids), comment=comment, status_db=status_db)
        status_db.commit_to_store()
    except CgError as error:
        status_db.rollback()
        LOG.error(error)
        raise click.Abort
