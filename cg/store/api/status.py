from datetime import datetime, timedelta
from types import SimpleNamespace
from typing import List, Optional, Tuple

from sqlalchemy.orm import Query
from typing_extensions import Literal

from cg.constants import CASE_ACTIONS, Pipeline, FlowCellStatus
from cg.constants.constants import CaseActions
from cg.store.models import (
    Analysis,
    Application,
    ApplicationVersion,
    Customer,
    Family,
    FamilySample,
    Pool,
    Sample,
    Flowcell,
)
from cg.store.status_analysis_filters import apply_analysis_filter
from cg.store.status_case_filters import apply_case_filter
from cg.store.api.base import BaseHandler
from cg.store.status_flow_cell_filters import apply_flow_cell_filter, FlowCellFilters
from cg.store.status_sample_filters import apply_sample_filter


class StatusHandler(BaseHandler):
    """Handles status states for entities in the database."""

    def samples_to_receive(self, external=False) -> Query:
        """Fetch incoming samples."""
        return (
            self.Sample.query.join(
                Sample.application_version,
                ApplicationVersion.application,
            )
            .filter(
                Sample.received_at.is_(None),
                Sample.downsampled_to.is_(None),
                Application.is_external == external,
            )
            .order_by(Sample.ordered_at)
        )

    def samples_to_prepare(self) -> Query:
        """Fetch samples in lab prep queue."""
        return (
            self.Sample.query.join(
                Sample.application_version,
                ApplicationVersion.application,
            )
            .filter(
                Sample.received_at.isnot(None),
                Sample.prepared_at.is_(None),
                Sample.downsampled_to.is_(None),
                Application.is_external == False,
                Sample.sequenced_at.is_(None),
            )
            .order_by(Sample.received_at)
        )

    def samples_to_sequence(self) -> Query:
        """Fetch samples in sequencing."""
        return (
            self.Sample.query.join(
                Sample.application_version,
                ApplicationVersion.application,
            )
            .filter(
                Sample.prepared_at.isnot(None),
                Sample.sequenced_at.is_(None),
                Sample.downsampled_to.is_(None),
                Application.is_external == False,
            )
            .order_by(Sample.received_at)
        )

    def get_families_with_analyses(self) -> Query:
        """Return all cases in the database with an analysis."""
        return self.Family.query.outerjoin(Analysis).join(
            Family.links,
            FamilySample.sample,
            ApplicationVersion,
            Application,
        )

    def get_families_with_samples(self) -> Query:
        """Return all cases in the database with samples."""
        return self.Family.query.join(Family.links, FamilySample.sample, Family.customer)

    def cases_to_analyze(
        self, pipeline: Pipeline = None, threshold: bool = False, limit: int = None
    ) -> List[Family]:
        """Returns a list if cases ready to be analyzed or set to be reanalyzed."""
        case_filter_functions: List[str] = [
            "get_cases_has_sequence",
            "get_cases_with_pipeline",
            "get_cases_for_analysis",
        ]
        cases = apply_case_filter(
            functions=case_filter_functions,
            cases=self.get_families_with_analyses(),
            pipeline=pipeline,
        )

        families: List[Query] = list(cases.order_by(Family.ordered_at))
        families = [
            case_obj
            for case_obj in families
            if case_obj.latest_sequenced
            and (
                case_obj.action == CaseActions.ANALYZE
                or not case_obj.latest_analyzed
                or case_obj.latest_analyzed < case_obj.latest_sequenced
            )
        ]

        if threshold:
            families = [case_obj for case_obj in families if case_obj.all_samples_pass_qc]
        return families[:limit]

    def cases_to_store(self, pipeline: Pipeline, limit: int = None) -> list:
        """Returns a list of cases that may be available to store in Housekeeper."""
        families_query = (
            self.Family.query.outerjoin(Analysis)
            .join(Family.links, FamilySample.sample)
            .filter(Family.data_analysis == str(pipeline))
            .filter(Family.action == "running")
        )
        return list(families_query)[:limit]

    def get_running_cases_for_pipeline(self, pipeline: Pipeline) -> List[Family]:
        return (
            self.query(Family)
            .filter(Family.action == "running")
            .filter(Family.data_analysis == pipeline)
            .all()
        )

    def cases(
        self,
        internal_id: str = None,
        name: str = None,
        days: int = 0,
        case_action: Optional[str] = None,
        priority: str = None,
        customer_id: str = None,
        exclude_customer_id: str = None,
        data_analysis: str = None,
        sample_id: str = None,
        only_received: bool = False,
        only_prepared: bool = False,
        only_sequenced: bool = False,
        only_analysed: bool = False,
        only_uploaded: bool = False,
        only_delivered: bool = False,
        only_delivery_reported: bool = False,
        only_invoiced: bool = False,
        exclude_received: bool = False,
        exclude_prepared: bool = False,
        exclude_sequenced: bool = False,
        exclude_analysed: bool = False,
        exclude_uploaded: bool = False,
        exclude_delivered: bool = False,
        exclude_delivery_reported: bool = False,
        exclude_invoiced: bool = False,
    ) -> List[Family]:
        """Fetch cases with and w/o analyses."""
        case_q = self._get_filtered_case_query(
            case_action,
            customer_id,
            data_analysis,
            days,
            exclude_customer_id,
            internal_id,
            name,
            priority,
            sample_id,
        )

        cases = []

        for case_obj in case_q:
            case_data = self._calculate_case_data(case_obj)

            skip_case = self._should_be_skipped(
                case_data,
                exclude_analysed,
                exclude_delivered,
                exclude_delivery_reported,
                exclude_invoiced,
                exclude_prepared,
                exclude_received,
                exclude_sequenced,
                exclude_uploaded,
                only_analysed,
                only_delivered,
                only_delivery_reported,
                only_invoiced,
                only_prepared,
                only_received,
                only_sequenced,
                only_uploaded,
            )

            if skip_case:
                continue

            case_output = self._get_case_output(case_data)

            cases.append(case_output)

        return sorted(cases, key=lambda k: k["tat"], reverse=True)

    def set_case_action(self, action: Literal[CASE_ACTIONS], case_id: str) -> None:
        """Sets the action of provided cases to None or the given action."""
        case_obj: Family = self.Family.query.filter(Family.internal_id == case_id).first()
        case_obj.action = action
        self.commit()

    def add_sample_comment(self, sample: Sample, comment: str) -> None:
        """Update comment on sample with the provided comment."""
        if sample.comment:
            sample.comment = sample.comment + " " + comment
        else:
            sample.comment = comment
        self.commit()

    def _get_analysis_case_query(self) -> Query:
        """Return analysis query."""
        return self.Analysis.query.join(Analysis.family)

    def _get_case_query(self) -> Query:
        """Return case query."""
        return self.query(Family)

    def _get_flow_cell_sample_links_query(self) -> Query:
        """Return flow cell query."""
        return self.Flowcell.query.join(Flowcell.samples, Sample.links)

    def get_flow_cells_by_case(self, case: Family) -> List[Flowcell]:
        """Return flow cells for case."""
        return apply_flow_cell_filter(
            flow_cells=self._get_flow_cell_sample_links_query(),
            functions=[FlowCellFilters.get_flow_cells_by_case],
            case=case,
        )

    def get_cases_to_compress(self, date_threshold: datetime) -> List[Family]:
        """Return all cases that are ready to be compressed by SPRING."""
        csse_filter_functions: List[str] = [
            "get_inactive_analysis_cases",
            "get_new_cases",
        ]
        return apply_case_filter(
            functions=csse_filter_functions, cases=self._get_case_query(), date=date_threshold
        )

    def _get_sample_query(self) -> Query:
        """Return sample query."""
        return self.query(Sample)

    def get_sample_by_id(self, entry_id: int) -> Sample:
        """Return a sample by entry id."""
        return apply_sample_filter(
            functions=["get_sample_by_entry_id"],
            samples=self._get_sample_query(),
            entry_id=entry_id,
        ).first()

    def sample(self, internal_id: str) -> Sample:
        """Return a sample by lims id."""
        return apply_sample_filter(
            functions=["get_sample_by_sample_id"],
            samples=self._get_sample_query(),
            internal_id=internal_id,
        ).first()

    @staticmethod
    def _get_case_output(case_data: SimpleNamespace) -> dict:
        return {
            "data_analysis": case_data.data_analysis,
            "internal_id": case_data.internal_id,
            "name": case_data.name,
            "ordered_at": case_data.ordered_at,
            "total_samples": case_data.total_samples,
            "total_external_samples": case_data.total_external_samples,
            "total_internal_samples": case_data.total_internal_samples,
            "case_external_bool": case_data.case_external_bool,
            "samples_to_receive": case_data.samples_to_receive,
            "samples_to_prepare": case_data.samples_to_prepare,
            "samples_to_sequence": case_data.samples_to_sequence,
            "samples_to_deliver": case_data.samples_to_deliver,
            "samples_to_invoice": case_data.samples_to_invoice,
            "samples_received": case_data.samples_received,
            "samples_prepared": case_data.samples_prepared,
            "samples_sequenced": case_data.samples_sequenced,
            "samples_received_at": case_data.samples_received_at,
            "samples_prepared_at": case_data.samples_prepared_at,
            "samples_sequenced_at": case_data.samples_sequenced_at,
            "samples_delivered_at": case_data.samples_delivered_at,
            "samples_invoiced_at": case_data.samples_invoiced_at,
            "case_action": case_data.case_action,
            "analysis_completed_at": case_data.analysis_completed_at,
            "analysis_uploaded_at": case_data.analysis_uploaded_at,
            "samples_delivered": case_data.samples_delivered,
            "analysis_delivery_reported_at": case_data.analysis_delivery_reported_at,
            "samples_invoiced": case_data.samples_invoiced,
            "analysis_pipeline": case_data.analysis_pipeline,
            "samples_received_bool": case_data.samples_received_bool,
            "samples_prepared_bool": case_data.samples_prepared_bool,
            "samples_sequenced_bool": case_data.samples_sequenced_bool,
            "analysis_completed_bool": case_data.analysis_completed_bool,
            "analysis_uploaded_bool": case_data.analysis_uploaded_bool,
            "samples_delivered_bool": case_data.samples_delivered_bool,
            "analysis_delivery_reported_bool": case_data.analysis_delivery_reported_bool,
            "samples_invoiced_bool": case_data.samples_invoiced_bool,
            "flowcells_status": case_data.flowcells_status,
            "flowcells_on_disk": case_data.flowcells_on_disk,
            "flowcells_on_disk_bool": case_data.flowcells_on_disk_bool,
            "tat": case_data.tat,
            "is_rerun": case_data.is_rerun,
            "max_tat": case_data.max_tat,
        }

    @staticmethod
    def _should_be_skipped(
        case_data: SimpleNamespace,
        exclude_analysed: bool,
        exclude_delivered: bool,
        exclude_delivery_reported: bool,
        exclude_invoiced: bool,
        exclude_prepared: bool,
        exclude_received: bool,
        exclude_sequenced: bool,
        exclude_uploaded: bool,
        only_analysed: bool,
        only_delivered: bool,
        only_delivery_reported: bool,
        only_invoiced: bool,
        only_prepared: bool,
        only_received: bool,
        only_sequenced: bool,
        only_uploaded: bool,
    ) -> bool:
        skip_case = False
        if only_received and not case_data.samples_received_bool:
            skip_case = True
        if only_prepared and not case_data.samples_prepared_bool:
            skip_case = True
        if only_sequenced and not case_data.samples_sequenced_bool:
            skip_case = True
        if only_analysed and not case_data.analysis_completed_bool:
            skip_case = True
        if only_uploaded and not case_data.analysis_uploaded_bool:
            skip_case = True
        if only_delivered and not case_data.samples_delivered_bool:
            skip_case = True
        if only_delivery_reported and not case_data.analysis_delivery_reported_bool:
            skip_case = True
        if only_invoiced and not case_data.samples_invoiced_bool:
            skip_case = True
        if exclude_received and case_data.samples_received_bool:
            skip_case = True
        if exclude_prepared and case_data.samples_prepared_bool:
            skip_case = True
        if exclude_sequenced and case_data.samples_sequenced_bool:
            skip_case = True
        if exclude_analysed and case_data.analysis_completed_bool:
            skip_case = True
        if exclude_uploaded and case_data.analysis_uploaded_bool:
            skip_case = True
        if exclude_delivered and case_data.samples_delivered_bool:
            skip_case = True
        if exclude_delivery_reported and case_data.analysis_delivery_reported_bool:
            skip_case = True
        if exclude_invoiced and case_data.samples_invoiced_bool:
            skip_case = True
        return skip_case

    def _calculate_case_data(self, case_obj: Family) -> SimpleNamespace:
        case_data = self._get_empty_case_data()

        case_data.data_analysis = case_obj.data_analysis
        case_data.internal_id = case_obj.internal_id
        case_data.name = case_obj.name
        case_data.ordered_at = case_obj.ordered_at

        case_data.analysis_in_progress = case_obj.action == "analyze"
        case_data.case_action = case_obj.action
        case_data.total_samples = len(case_obj.links)
        case_data.total_external_samples = len(
            [
                link.sample.application_version.application.is_external
                for link in case_obj.links
                if link.sample.application_version.application.is_external
            ]
        )
        case_data.total_internal_samples = (
            case_data.total_samples - case_data.total_external_samples
        )
        case_data.case_external_bool = case_data.total_external_samples == case_data.total_samples
        if case_data.total_samples > 0:
            case_data.samples_received = len(
                [link.sample.received_at for link in case_obj.links if link.sample.received_at]
            )
            case_data.samples_prepared = len(
                [link.sample.prepared_at for link in case_obj.links if link.sample.prepared_at]
            )
            case_data.samples_sequenced = len(
                [link.sample.sequenced_at for link in case_obj.links if link.sample.sequenced_at]
            )
            case_data.samples_delivered = len(
                [link.sample.delivered_at for link in case_obj.links if link.sample.delivered_at]
            )
            case_data.samples_invoiced = len(
                [
                    link.sample.invoice.invoiced_at
                    for link in case_obj.links
                    if link.sample.invoice and link.sample.invoice.invoiced_at
                ]
            )

            case_data.samples_to_receive = case_data.total_internal_samples
            case_data.samples_to_prepare = case_data.total_internal_samples
            case_data.samples_to_sequence = case_data.total_internal_samples
            case_data.samples_to_deliver = case_data.total_internal_samples
            case_data.samples_to_invoice = case_data.total_samples - len(
                [link.sample.no_invoice for link in case_obj.links if link.sample.no_invoice]
            )

            case_data.samples_received_bool = (
                case_data.samples_received == case_data.samples_to_receive
            )
            case_data.samples_prepared_bool = (
                case_data.samples_prepared == case_data.samples_to_prepare
            )
            case_data.samples_sequenced_bool = (
                case_data.samples_sequenced == case_data.samples_to_sequence
            )
            case_data.samples_delivered_bool = (
                case_data.samples_delivered == case_data.samples_to_deliver
            )
            case_data.samples_invoiced_bool = (
                case_data.samples_invoiced == case_data.samples_to_invoice
            )

            if case_data.samples_to_receive > 0 and case_data.samples_received_bool:
                case_data.samples_received_at = max(
                    link.sample.received_at
                    for link in case_obj.links
                    if link.sample.received_at is not None
                )

            if case_data.samples_to_prepare > 0 and case_data.samples_prepared_bool:
                case_data.samples_prepared_at = max(
                    link.sample.prepared_at
                    for link in case_obj.links
                    if link.sample.prepared_at is not None
                )

            if case_data.samples_to_sequence > 0 and case_data.samples_sequenced_bool:
                case_data.samples_sequenced_at = max(
                    link.sample.sequenced_at
                    for link in case_obj.links
                    if link.sample.sequenced_at is not None
                )

            if case_data.samples_to_deliver > 0 and case_data.samples_delivered_bool:
                case_data.samples_delivered_at = max(
                    link.sample.delivered_at
                    for link in case_obj.links
                    if link.sample.delivered_at is not None
                )

            if case_data.samples_to_invoice > 0 and case_data.samples_invoiced_bool:
                case_data.samples_invoiced_at = max(
                    link.sample.invoice.invoiced_at
                    for link in case_obj.links
                    if link.sample.invoice and link.sample.invoice.invoiced_at
                )

            case_data.flowcells = len(list(self.get_flow_cells_by_case(case=case_obj)))
            case_data.flowcells_status = [
                flow_cell.status for flow_cell in self.get_flow_cells_by_case(case=case_obj)
            ]
            case_data.flowcells_on_disk = len(
                [
                    status
                    for status in case_data.flowcells_status
                    if status == FlowCellStatus.ON_DISK
                ]
            )

            if case_data.flowcells < case_data.total_samples:
                case_data.flowcells_status.append("new")

            case_data.flowcells_status = ", ".join(case_data.flowcells_status)

            case_data.flowcells_on_disk_bool = (
                case_data.flowcells_on_disk == case_data.total_samples
            )
        if case_obj.analyses and not case_data.analysis_in_progress:
            case_data.analysis_completed_at = case_obj.analyses[0].completed_at
            case_data.analysis_uploaded_at = case_obj.analyses[0].uploaded_at
            case_data.analysis_delivery_reported_at = case_obj.analyses[
                0
            ].delivery_report_created_at
            case_data.analysis_pipeline = case_obj.analyses[0].pipeline
            case_data.analysis_completed_bool = case_data.analysis_completed_at is not None
            case_data.analysis_uploaded_bool = case_data.analysis_uploaded_at is not None
            case_data.analysis_delivery_reported_bool = (
                case_data.analysis_delivery_reported_at is not None
            )
        elif case_data.total_samples > 0:
            case_data.analysis_completed_bool = False
            case_data.analysis_uploaded_bool = False
            case_data.analysis_delivery_reported_bool = False

        case_data.is_rerun = self._is_rerun(
            case_obj,
            case_data.samples_received_at,
            case_data.samples_prepared_at,
            case_data.samples_sequenced_at,
        )
        case_data.tat = self._calculate_estimated_turnaround_time(
            case_data.is_rerun,
            case_data.case_external_bool,
            case_obj.ordered_at,
            case_data.samples_received_at,
            case_data.samples_prepared_at,
            case_data.samples_sequenced_at,
            case_data.analysis_completed_at,
            case_data.analysis_uploaded_at,
            case_data.samples_delivered_at,
        )
        case_data.max_tat = self._get_max_tat(links=case_obj.links)
        return case_data

    def _get_filtered_case_query(
        self,
        case_action: Optional[str],
        customer_id: str,
        data_analysis: str,
        days: int,
        exclude_customer_id: bool,
        internal_id: str,
        name: str,
        priority: str,
        sample_id: str,
    ) -> Query:
        case_q = self.Family.query
        # family filters
        if days != 0:
            filter_date = datetime.now() - timedelta(days=days)
            case_q = case_q.filter(Family.ordered_at > filter_date)
        if case_action:
            case_q = case_q.filter(Family.action == case_action)
        if priority:
            case_q = case_q.filter(Family.priority == priority)
        if internal_id:
            case_q = case_q.filter(Family.internal_id.ilike(f"%{internal_id}%"))
        if name:
            case_q = case_q.filter(Family.name.ilike(f"%{name}%"))
        if data_analysis:
            case_q = case_q.filter(Family.data_analysis.ilike(f"%{data_analysis}%"))
        # customer filters
        if customer_id or exclude_customer_id:
            case_q = case_q.join(Family.customer)

        if customer_id:
            case_q = case_q.filter(Customer.internal_id == customer_id)

        if exclude_customer_id:
            case_q = case_q.filter(Customer.internal_id != exclude_customer_id)
        # sample filters
        if sample_id:
            case_q = case_q.join(Family.links, FamilySample.sample)
            case_q = case_q.filter(Sample.internal_id.ilike(f"%{sample_id}%"))
        else:
            case_q = case_q.outerjoin(Family.links, FamilySample.sample)
        # other joins
        case_q = case_q.outerjoin(Family.analyses, Sample.invoice, Sample.flowcells)
        return case_q

    @staticmethod
    def _is_rerun(
        case_obj: Family,
        samples_received_at: datetime,
        samples_prepared_at: datetime,
        samples_sequenced_at: datetime,
    ) -> bool:
        return (
            (len(case_obj.analyses) > 0)
            or (samples_received_at and samples_received_at < case_obj.ordered_at)
            or (samples_prepared_at and samples_prepared_at < case_obj.ordered_at)
            or (samples_sequenced_at and samples_sequenced_at < case_obj.ordered_at)
        )

    @staticmethod
    def _all_samples_have_sequence_data(links: List[FamilySample]) -> bool:
        """Return True if all samples are external or sequenced in-house."""
        return all(
            (link.sample.sequenced_at or link.sample.application_version.application.is_external)
            for link in links
        )

    def analyses_to_upload(self, pipeline: Pipeline = None) -> List[Analysis]:
        """Return analyses that have not been uploaded."""
        analysis_filter_functions: List[str] = [
            "get_analyses_with_pipeline",
            "get_completed_analyses",
            "get_not_uploaded_analyses",
            "get_valid_analyses_in_production",
            "order_analyses_by_completed_at",
        ]
        return apply_analysis_filter(
            functions=analysis_filter_functions,
            analyses=self._get_analysis_case_query(),
            pipeline=pipeline,
        )

    def analyses_to_clean(
        self, before: datetime = datetime.now(), pipeline: Pipeline = None
    ) -> Query:
        """Fetch analyses that haven't been cleaned."""
        records = self.latest_analyses()
        records = records.filter(
            Analysis.uploaded_at.isnot(None),
            Analysis.cleaned_at.is_(None),
            Analysis.started_at <= before,
            Family.action.is_(None),
        )
        if pipeline:
            records = records.filter(
                Analysis.pipeline == str(pipeline),
            )

        return records

    def get_analyses_before_date(
        self,
        case_id: Optional[str] = None,
        before: Optional[datetime] = datetime.now(),
        pipeline: Optional[Pipeline] = None,
    ) -> Query:
        """Fetch all analyses older than certain date."""
        records: Query = self._get_analysis_case_query()
        if case_id:
            records = records.filter(Family.internal_id == case_id)
        if pipeline:
            records = records.filter(
                Analysis.pipeline == str(pipeline),
            )
        records = records.filter(Analysis.started_at <= before)
        return records

    def observations_to_upload(self, pipeline: Pipeline = None) -> Query:
        """Return observations that have not been uploaded."""
        case_filter_functions: List[str] = [
            "get_cases_with_loqusdb_supported_pipeline",
            "get_cases_with_loqusdb_supported_sequencing_method",
        ]
        records: Query = apply_case_filter(
            functions=case_filter_functions,
            cases=self.get_families_with_samples(),
            pipeline=pipeline,
        )
        return apply_sample_filter(functions=["get_samples_without_loqusdb_id"], samples=records)

    def observations_uploaded(self, pipeline: Pipeline = None) -> Query:
        """Return observations that have been uploaded."""
        records: Query = apply_case_filter(
            functions=["get_cases_with_loqusdb_supported_pipeline"],
            cases=self.get_families_with_samples(),
            pipeline=pipeline,
        )
        records: Query = apply_sample_filter(
            functions=["get_samples_with_loqusdb_id"], samples=records
        )
        return records

    def analyses_to_deliver(self, pipeline: Pipeline = None) -> Query:
        """Fetch analyses that have been uploaded but not delivered."""
        return (
            self.Analysis.query.join(Family, Family.links, FamilySample.sample)
            .filter(
                Analysis.uploaded_at.isnot(None),
                Sample.delivered_at.is_(None),
                Analysis.pipeline == str(pipeline),
            )
            .order_by(Analysis.uploaded_at.desc())
        )

    def analyses_to_delivery_report(self, pipeline: Pipeline = None) -> Query:
        """Return analyses that need a delivery report to be regenerated."""
        records: Query = apply_case_filter(
            functions=["get_report_cases_with_valid_data_delivery"],
            cases=self._get_analysis_case_query(),
            pipeline=pipeline,
        )
        analysis_filter_functions: List[str] = [
            "get_report_analyses_by_pipeline",
            "get_analyses_without_delivery_report",
            "get_valid_analyses_in_production",
            "order_analyses_by_completed_at",
        ]
        return apply_analysis_filter(
            functions=analysis_filter_functions, analyses=records, pipeline=pipeline
        )

    def analyses_to_upload_delivery_reports(self, pipeline: Pipeline = None) -> Query:
        """Return analyses that need a delivery report to be uploaded."""
        records: Query = apply_case_filter(
            functions=["get_cases_with_scout_data_delivery"],
            cases=self._get_analysis_case_query(),
            pipeline=pipeline,
        )
        analysis_filter_functions: List[str] = [
            "get_report_analyses_by_pipeline",
            "get_analyses_with_delivery_report",
            "get_not_uploaded_analyses",
            "get_valid_analyses_in_production",
            "order_analyses_by_completed_at",
        ]
        return apply_analysis_filter(
            functions=analysis_filter_functions, analyses=records, pipeline=pipeline
        )

    def samples_to_deliver(self) -> Query:
        """Fetch samples that have been sequenced but not delivered."""
        return self.Sample.query.filter(
            Sample.sequenced_at.isnot(None),
            Sample.delivered_at.is_(None),
            Sample.downsampled_to.is_(None),
        )

    def samples_not_delivered(self) -> Query:
        """Fetch samples not delivered."""
        return self.Sample.query.filter(
            Sample.delivered_at.is_(None), Sample.downsampled_to.is_(None)
        )

    def samples_not_invoiced(self) -> Query:
        """Fetch all samples that are not invoiced."""
        return self.Sample.query.filter(
            Sample.downsampled_to.is_(None), Sample.invoice_id.is_(None)
        )

    def samples_not_downsampled(self) -> Query:
        """Fetch all samples that are not down sampled."""
        return self.Sample.query.filter(Sample.downsampled_to.is_(None))

    def microbial_samples_to_invoice(self, customer: Customer = None) -> Tuple[Query, list]:
        """Fetch microbial samples that should be invoiced.

        Returns microbial samples that have been delivered but not invoiced.
        """
        records = self.Sample.query.filter(
            str(Pipeline.MICROSALT) in self.Family.data_analysis,
            Sample.delivered_at is not None,
            Sample.invoice_id.is_(None),
        )
        customers_to_invoice = list({case_obj.customer for case_obj in records.all()})
        if customer:
            records = records.join(Family).filter(Family.customer_id == customer.id)
        return records, customers_to_invoice

    def samples_to_invoice(self, customer: Customer = None) -> Tuple[Query, list]:
        """Fetch samples that should be invoiced.

        Returns samples have been delivered but not invoiced, excluding those that
        have been marked to skip invoicing.
        """
        records = self.Sample.query.filter(
            Sample.delivered_at.isnot(None),
            Sample.invoice_id.is_(None),
            Sample.no_invoice == False,
            Sample.downsampled_to.is_(None),
        )
        customers_to_invoice = [
            case_obj.customer
            for case_obj in records.all()
            if case_obj.customer.internal_id != "cust000"
        ]

        customers_to_invoice = list(set(customers_to_invoice))
        records = records.filter(Sample.customer == customer) if customer else records
        return records, customers_to_invoice

    def pools_to_invoice(self, customer: Customer = None) -> Tuple[Query, list]:
        """
        Fetch pools that should be invoiced.
        """
        records = self.Pool.query.filter(
            Pool.invoice_id.is_(None),
            Pool.no_invoice == False,
            Pool.delivered_at.isnot(None),
        )

        customers_to_invoice = [
            case_obj.customer
            for case_obj in records.all()
            if case_obj.customer.internal_id != "cust000"
        ]

        customers_to_invoice = list(set(customers_to_invoice))
        records = records.filter(Pool.customer_id == customer.id) if customer else records
        return records, customers_to_invoice

    def pools_to_receive(self) -> Query:
        """Fetch pools that have been not yet been received."""
        return self.Pool.query.filter(Pool.received_at.is_(None))

    def pools_to_deliver(self) -> Query:
        """Fetch pools that have been not yet been delivered."""
        return self.Pool.query.filter(Pool.received_at.isnot(None), Pool.delivered_at.is_(None))

    def _calculate_estimated_turnaround_time(
        self,
        is_rerun,
        external_case_bool,
        analysis_ordered_at,
        samples_received_at,
        samples_prepared_at,
        samples_sequenced_at,
        analysis_completed_at,
        analysis_uploaded_at,
        samples_delivered_at,
    ) -> timedelta:
        """Calculated estimated turnaround-time."""
        if samples_received_at and samples_delivered_at:
            return self._calculate_date_delta(None, samples_received_at, samples_delivered_at)

        o_a = self._calculate_date_delta(5, analysis_ordered_at, analysis_completed_at)
        r_p = self._calculate_date_delta(4, samples_received_at, samples_prepared_at)
        p_s = self._calculate_date_delta(5, samples_prepared_at, samples_sequenced_at)
        s_a = self._calculate_date_delta(4, samples_sequenced_at, analysis_completed_at)
        a_u = self._calculate_date_delta(1, analysis_completed_at, analysis_uploaded_at)
        u_d = self._calculate_date_delta(2, analysis_uploaded_at, samples_delivered_at)

        if is_rerun:
            o_a = self._calculate_date_delta(1, analysis_ordered_at, analysis_completed_at)
            return o_a + a_u

        if external_case_bool:
            if analysis_ordered_at and analysis_uploaded_at:
                return self._calculate_date_delta(None, analysis_ordered_at, analysis_uploaded_at)

            return o_a + a_u

        if samples_received_at and samples_delivered_at:
            return self._calculate_date_delta(None, samples_received_at, samples_delivered_at)

        return r_p + p_s + s_a + a_u + u_d

    @staticmethod
    def _calculate_date_delta(default, first_date, last_date) -> timedelta:
        # calculates date delta between two dates, assumes last_date is today if missing
        delta = default
        if not last_date:
            last_date = datetime.now()
        if first_date:
            delta = (last_date - first_date).days
        return delta

    @staticmethod
    def _get_max_tat(links) -> int:
        max_tat = 0
        for link in links:
            if link.sample.application_version.application.turnaround_time:
                max_tat = max(0, link.sample.application_version.application.turnaround_time)
        return max_tat

    @staticmethod
    def _get_empty_case_data() -> SimpleNamespace:
        case_data = SimpleNamespace()
        case_data.data_analysis = None
        case_data.internal_id = None
        case_data.name = None
        case_data.ordered_at = None
        case_data.total_samples = None
        case_data.total_external_samples = None
        case_data.total_internal_samples = None
        case_data.case_external_bool = None
        case_data.samples_to_receive = None
        case_data.samples_to_prepare = None
        case_data.samples_to_sequence = None
        case_data.samples_to_deliver = None
        case_data.samples_to_invoice = None
        case_data.samples_received = None
        case_data.samples_prepared = None
        case_data.samples_sequenced = None
        case_data.samples_received_at = None
        case_data.samples_prepared_at = None
        case_data.samples_sequenced_at = None
        case_data.samples_delivered_at = None
        case_data.samples_invoiced_at = None
        case_data.case_action = None
        case_data.analysis_completed_at = None
        case_data.analysis_uploaded_at = None
        case_data.samples_delivered = None
        case_data.analysis_delivery_reported_at = None

        case_data.samples_invoiced = None
        case_data.analysis_pipeline = None
        case_data.samples_received_bool = None
        case_data.samples_prepared_bool = None
        case_data.samples_sequenced_bool = None
        case_data.analysis_completed_bool = None
        case_data.analysis_uploaded_bool = None
        case_data.samples_delivered_bool = None
        case_data.analysis_delivery_reported_bool = None
        case_data.samples_invoiced_bool = None
        case_data.flowcells_status = None
        case_data.flowcells_on_disk = None
        case_data.flowcells_on_disk_bool = None
        case_data.tat = None
        case_data.is_rerun = None
        case_data.max_tat = None

        return case_data
