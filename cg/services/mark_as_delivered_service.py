import logging
from datetime import datetime

from requests import Response

from cg.apps.tb.api import TrailblazerAPI
from cg.apps.tb.models import TrailblazerAnalysis
from cg.cli import workflow
from cg.constants import Workflow
from cg.store.models import Analysis, Case, CaseSample, Order, Sample
from cg.store.store import Store

LOG = logging.getLogger(__name__)


class MarkAsDeliveredService:
    def __init__(self, status_db: Store, trailblazer_api: TrailblazerAPI) -> None:
        self.status_db = status_db
        self.trailblazer_api = trailblazer_api

    def mark_analyses(
        self, analyses: list[Analysis], auth_token: str | None = None, signature: str | None = None
    ) -> Response:
        """Mark samples as delivered in StatusDB and the analysis as delivered in Trailblazer."""
        trailblazer_ids = []
        for analysis in analyses:
            self._mark_samples_in_analysis(analysis)
            trailblazer_ids.append(analysis.trailblazer_id)
        return self.trailblazer_api.mark_analyses_as_delivered(
            auth_token=auth_token, signature=signature, trailblazer_ids=trailblazer_ids
        )

    def close_order(self, order: Order):
        """
        Closes order IF
        - we have a delivered TB analysis for each case
        - each sample in the order has a "delivered_at" set

        Note, the second condition is only needed for partial deliveries in microSALT and taxprofiler.
        """
        delivered_analyses: list[TrailblazerAnalysis] = self.trailblazer_api.get_delivered_analyses(
            order_id=order.id
        )
        delivered_case_ids: set[str] = set(analysis.case_id for analysis in delivered_analyses)
        case_ids_on_order: set[str] = set(case.internal_id for case in order.cases)
        are_all_samples_delivered = all(
            sample.delivered_at for case in order.cases for sample in case.samples
        )
        if delivered_case_ids == case_ids_on_order and are_all_samples_delivered:
            order.is_open = False
            # TODO: Communicate with Freshdesk

    def _mark_samples_in_analysis(self, analysis: Analysis) -> None:
        case: Case = analysis.case
        LOG.info(f"Marking samples as delivered for case {case.internal_id}")
        for case_sample in case.links:
            if self._should_sample_be_delivered(case_sample):
                case_sample.sample.delivered_at = datetime.now()

    def _should_sample_be_delivered(self, case_sample: CaseSample) -> bool:
        return (
            case_sample.should_deliver_sample
            and not case_sample.sample.delivered_at
            and self._passes_on_reads(case_sample)
        )

    @staticmethod
    def _passes_on_reads(case_sample: CaseSample) -> bool:
        """
        Return True if the sample associated with the case has enough reads to be delivered.
        This check is only relevant for microSALT and Taxprofiler samples that are not negative
        controls, as those pipelines are the only ones that allow partial delivery of samples.
        For the rest of the pipelines, the samples will always have enough reads.
        """
        case: Case = case_sample.case
        sample: Sample = case_sample.sample
        if (
            case.data_analysis in [Workflow.MICROSALT, Workflow.TAXPROFILER]
            and not sample.is_negative_control
        ):
            return sample.reads >= sample.expected_reads_for_sample  # type: ignore Illumina sample
        else:
            return True
