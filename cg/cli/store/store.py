import logging

import rich_click as click

from cg.clients.arnold.exceptions import ArnoldClientError, ArnoldServerError
from cg.clients.janus.exceptions import JanusClientError, JanusServerError
from cg.constants.cli_options import DRY_RUN
from cg.meta.qc_metrics.collect_qc_metrics import CollectQCMetricsAPI
from cg.models.cg_config import CGConfig

LOG = logging.getLogger(__name__)


@click.command("qc-metrics")
@click.argument("case-id", type=str)
@DRY_RUN
@click.pass_obj
def store_qc_metrics(config: CGConfig, case_id: str, dry_run: bool = False) -> None:
    """Fetch the QC metrics for a case from Janus and Store them in Arnold."""
    metrics_api = CollectQCMetricsAPI(
        hk_api=config.housekeeper_api,
        status_db=config.status_db,
        janus_api=config.janus_api,
        arnold_api=config.arnold_api,
    )
    try:
        metrics_api.create_case(case_id=case_id, dry_run=dry_run)
    except (JanusClientError, JanusServerError, ArnoldClientError, ArnoldServerError):
        return
