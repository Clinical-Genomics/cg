from datetime import datetime, timedelta
from types import SimpleNamespace
from typing import List, Optional, Tuple

from cg.constants import PRIORITY_MAP, Pipeline
from cg.store import models
from cg.store.api.base import BaseHandler
from cg.utils.date import get_date
from sqlalchemy import and_, or_
from sqlalchemy.orm import Query

VALID_DATA_IN_PRODUCTION = get_date("2017-09-27")


class StatusHandler(BaseHandler):
    """Handles status states for entities in the database"""

    def samples_to_receive(self, external=False) -> Query:
        """Fetch incoming samples."""
        return (
            self.Sample.query.join(
                models.Sample.application_version,
                models.ApplicationVersion.application,
            )
            .filter(
                models.Sample.received_at.is_(None),
                models.Sample.downsampled_to.is_(None),
                models.Application.is_external == external,
            )
            .order_by(models.Sample.ordered_at)
        )

    def samples_to_prepare(self) -> Query:
        """Fetch samples in lab prep queue."""
        return (
            self.Sample.query.join(
                models.Sample.application_version,
                models.ApplicationVersion.application,
            )
            .filter(
                models.Sample.received_at.isnot(None),
                models.Sample.prepared_at.is_(None),
                models.Sample.downsampled_to.is_(None),
                models.Application.is_external == False,
                models.Sample.sequenced_at.is_(None),
            )
            .order_by(models.Sample.priority.desc(), models.Sample.received_at)
        )

    def samples_to_sequence(self) -> Query:
        """Fetch samples in sequencing."""
        return (
            self.Sample.query.join(
                models.Sample.application_version,
                models.ApplicationVersion.application,
            )
            .filter(
                models.Sample.prepared_at.isnot(None),
                models.Sample.sequenced_at.is_(None),
                models.Sample.downsampled_to.is_(None),
                models.Application.is_external == False,
            )
            .order_by(models.Sample.priority.desc(), models.Sample.received_at)
        )

    def cases_to_analyze(
        self, pipeline: Pipeline = None, threshold: bool = False, limit: int = None
    ) -> List[models.Family]:
        """Returns a list if cases ready to be analyzed or set to be reanalyzed"""
        families_query = list(
            self.Family.query.outerjoin(models.Analysis)
            .join(models.Family.links, models.FamilySample.sample)
            .filter(or_(models.Sample.is_external, models.Sample.sequenced_at.isnot(None)))
            .filter(models.Family.data_analysis == str(pipeline))
            .filter(
                or_(
                    models.Family.action == "analyze",
                    and_(models.Family.action.is_(None), models.Analysis.created_at.is_(None)),
                    and_(
                        models.Family.action.is_(None),
                        models.Analysis.created_at < models.Sample.sequenced_at,
                    ),
                )
            )
            .order_by(models.Family.priority.desc(), models.Family.ordered_at)
        )
        families_query = [
            case_obj
            for case_obj in families_query
            if case_obj.latest_sequenced
            and (
                case_obj.action == "analyze"
                or not case_obj.latest_analyzed
                or case_obj.latest_analyzed < case_obj.latest_sequenced
            )
        ]

        if threshold:
            families_query = [
                case_obj for case_obj in families_query if case_obj.all_samples_pass_qc
            ]
        return families_query[:limit]

    def cases_to_store(self, pipeline: Pipeline, limit: int = None) -> list:
        """Returns a list of cases that may be available to store in Housekeeper"""
        families_query = (
            self.Family.query.outerjoin(models.Analysis)
            .join(models.Family.links, models.FamilySample.sample)
            .filter(models.Family.data_analysis == str(pipeline))
            .filter(models.Family.action == "running")
        )
        return list(families_query)[:limit]

    def get_running_cases_for_pipeline(self, pipeline: Pipeline) -> List[models.Family]:
        return (
            self.query(models.Family)
            .filter(models.Family.action == "running")
            .filter(models.Family.data_analysis == pipeline)
            .all()
        )

    def get_cases_from_ticket(self, ticket_id: int) -> Query:
        return self.Family.query.join(models.Family.links, models.FamilySample.sample).filter(
            models.Sample.ticket_number == ticket_id
        )

    def get_samples_from_ticket(self, ticket_id: int) -> List[models.Sample]:
        return self.query(models.Sample).filter(models.Sample.ticket_number == ticket_id).all()

    def get_samples_from_flowcell(self, flowcell_id: str) -> List[models.Sample]:
        flowcell = self.query(models.Flowcell).filter(models.Flowcell.name == flowcell_id).first()
        if flowcell:
            return flowcell.samples

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
    ) -> List[models.Family]:
        """Fetch cases with and w/o analyses"""
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

    def _calculate_case_data(self, case_obj: models.Family) -> SimpleNamespace:
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

            case_data.flowcells = len(
                [flowcell.status for link in case_obj.links for flowcell in link.sample.flowcells]
            )

            case_data.flowcells_status = list(
                {flowcell.status for link in case_obj.links for flowcell in link.sample.flowcells}
            )

            if case_data.flowcells < case_data.total_samples:
                case_data.flowcells_status.append("new")

            case_data.flowcells_status = ", ".join(case_data.flowcells_status)

            case_data.flowcells_on_disk = len(
                [
                    flowcell.status
                    for link in case_obj.links
                    for flowcell in link.sample.flowcells
                    if flowcell.status == "ondisk"
                ]
            )

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
            case_q = case_q.filter(models.Family.ordered_at > filter_date)
        if case_action:
            case_q = case_q.filter(models.Family.action == case_action)
        if priority:
            priority_db = PRIORITY_MAP[priority]
            case_q = case_q.filter(models.Family.priority == priority_db)
        if internal_id:
            case_q = case_q.filter(models.Family.internal_id.ilike(f"%{internal_id}%"))
        if name:
            case_q = case_q.filter(models.Family.name.ilike(f"%{name}%"))
        if data_analysis:
            case_q = case_q.filter(models.Family.data_analysis.ilike(f"%{data_analysis}%"))
        # customer filters
        if customer_id or exclude_customer_id:
            case_q = case_q.join(models.Family.customer)

        if customer_id:
            case_q = case_q.filter(models.Customer.internal_id == customer_id)

        if exclude_customer_id:
            case_q = case_q.filter(models.Customer.internal_id != exclude_customer_id)
        # sample filters
        if sample_id:
            case_q = case_q.join(models.Family.links, models.FamilySample.sample)
            case_q = case_q.filter(models.Sample.internal_id.ilike(f"%{sample_id}%"))
        else:
            case_q = case_q.outerjoin(models.Family.links, models.FamilySample.sample)
        # other joins
        case_q = case_q.outerjoin(
            models.Family.analyses, models.Sample.invoice, models.Sample.flowcells
        )
        return case_q

    @staticmethod
    def _is_rerun(
        case_obj: models.Family,
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
    def _all_samples_have_sequence_data(links: List[models.FamilySample]) -> bool:
        """Return True if all samples are external or sequenced in-house."""
        return all((link.sample.sequenced_at or link.sample.is_external) for link in links)

    def analyses_to_upload(self, pipeline: Pipeline = None) -> List[models.Analysis]:
        """Fetch analyses that haven't been uploaded."""
        records = self.Analysis.query.filter(
            models.Analysis.completed_at.isnot(None), models.Analysis.uploaded_at.is_(None)
        )

        if pipeline:
            records = records.filter(models.Analysis.pipeline == str(pipeline))

        return records

    def analyses_to_clean(
        self, before: datetime = datetime.now(), pipeline: Pipeline = None
    ) -> Query:
        """Fetch analyses that haven't been cleaned."""
        records = self.latest_analyses()
        records = records.filter(
            models.Analysis.uploaded_at.isnot(None),
            models.Analysis.cleaned_at.is_(None),
            models.Analysis.started_at <= before,
            models.Family.action.is_(None),
        )
        if pipeline:
            records = records.filter(
                models.Analysis.pipeline == str(pipeline),
            )

        return records

    def observations_to_upload(self):
        """Fetch observations that haven't been uploaded."""

        return self.Family.query.join(
            models.Analysis, models.Family.links, models.FamilySample.sample
        ).filter(models.Sample.loqusdb_id.is_(None))

    def observations_uploaded(self) -> Query:
        """Fetch observations that have been uploaded."""

        return self.Family.query.join(models.Family.links, models.FamilySample.sample).filter(
            models.Sample.loqusdb_id.isnot(None)
        )

    def analyses_to_deliver(self, pipeline: Pipeline = None) -> Query:
        """Fetch analyses that have been uploaded but not delivered."""
        return (
            self.Analysis.query.join(models.Family, models.Family.links, models.FamilySample.sample)
            .filter(
                models.Analysis.uploaded_at.isnot(None),
                models.Sample.delivered_at.is_(None),
                models.Analysis.pipeline == str(pipeline),
            )
            .order_by(models.Analysis.uploaded_at.desc())
        )

    def analyses_to_delivery_report(self, pipeline: Pipeline = None) -> Query:
        """Fetch analyses that needs the delivery report to be regenerated."""

        analyses_query = self.latest_analyses()

        analyses_query = (
            analyses_query.filter(models.Analysis.uploaded_at)
            .filter(VALID_DATA_IN_PRODUCTION < models.Analysis.started_at)
            .join(models.Family, models.Family.links, models.FamilySample.sample)
            .filter(
                or_(
                    models.Family.data_analysis.is_(None),
                    models.Family.data_analysis == str(pipeline),
                )
            )
            .filter(
                models.Sample.delivered_at.isnot(None),
                or_(
                    models.Analysis.delivery_report_created_at.is_(None),
                    and_(
                        models.Analysis.delivery_report_created_at.isnot(None),
                        models.Analysis.delivery_report_created_at < models.Sample.delivered_at,
                    ),
                ),
            )
            .order_by(models.Analysis.uploaded_at.desc())
        )
        return analyses_query

    def samples_to_deliver(self) -> Query:
        """Fetch samples that have been sequenced but not delivered."""
        return self.Sample.query.filter(
            models.Sample.sequenced_at.isnot(None),
            models.Sample.delivered_at.is_(None),
            models.Sample.downsampled_to.is_(None),
        )

    def samples_not_delivered(self) -> Query:
        """Fetch samples not delivered."""
        return self.Sample.query.filter(
            models.Sample.delivered_at.is_(None), models.Sample.downsampled_to.is_(None)
        )

    def samples_not_invoiced(self) -> Query:
        """Fetch all samples that are not invoiced."""
        return self.Sample.query.filter(
            models.Sample.downsampled_to.is_(None), models.Sample.invoice_id.is_(None)
        )

    def samples_not_downsampled(self) -> Query:
        """Fetch all samples that are not down sampled."""
        return self.Sample.query.filter(models.Sample.downsampled_to.is_(None))

    def microbial_samples_to_invoice(self, customer: models.Customer = None) -> Tuple[Query, list]:
        """Fetch microbial samples that should be invoiced.

        Returns microbial samples that have been delivered but not invoiced.
        """
        records = self.Sample.query.filter(
            str(Pipeline.MICROSALT) in self.Family.data_analysis,
            models.Sample.delivered_at is not None,
            models.Sample.invoice_id.is_(None),
        )
        customers_to_invoice = list({case_obj.customer for case_obj in records.all()})
        if customer:
            records = records.join(models.Family).filter(models.Family.customer_id == customer.id)
        return records, customers_to_invoice

    def samples_to_invoice(self, customer: models.Customer = None) -> Tuple[Query, list]:
        """Fetch samples that should be invoiced.

        Returns samples have been delivered but not invoiced, excluding those that
        have been marked to skip invoicing.
        """
        records = self.Sample.query.filter(
            models.Sample.delivered_at.isnot(None),
            models.Sample.invoice_id.is_(None),
            models.Sample.no_invoice == False,
            models.Sample.downsampled_to.is_(None),
        )
        customers_to_invoice = [
            case_obj.customer
            for case_obj in records.all()
            if case_obj.customer.internal_id != "cust000"
        ]

        customers_to_invoice = list(set(customers_to_invoice))
        records = records.filter(models.Sample.customer == customer) if customer else records
        return records, customers_to_invoice

    def pools_to_invoice(self, customer: models.Customer = None) -> Tuple[Query, list]:
        """
        Fetch pools that should be invoiced.
        """
        records = self.Pool.query.filter(
            models.Pool.invoice_id.is_(None),
            models.Pool.no_invoice == False,
            models.Pool.delivered_at.isnot(None),
        )

        customers_to_invoice = [
            case_obj.customer
            for case_obj in records.all()
            if case_obj.customer.internal_id != "cust000"
        ]

        customers_to_invoice = list(set(customers_to_invoice))
        records = records.filter(models.Pool.customer_id == customer.id) if customer else records
        return records, customers_to_invoice

    def pools_to_receive(self) -> Query:
        """Fetch pools that have been not yet been received."""
        return self.Pool.query.filter(models.Pool.received_at.is_(None))

    def pools_to_deliver(self) -> Query:
        """Fetch pools that have been not yet been delivered."""
        return self.Pool.query.filter(
            models.Pool.received_at.isnot(None), models.Pool.delivered_at.is_(None)
        )

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
        """Calculated estimated turnaround-time"""
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
