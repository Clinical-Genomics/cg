from datetime import datetime, timedelta
from types import SimpleNamespace
from typing import List

from cg.constants import PRIORITY_MAP
from cg.store import models
from cg.store.api.base import BaseHandler
from cg.utils.date import get_date
from sqlalchemy import or_, and_
from sqlalchemy.orm import Query

VALID_DATA_IN_PRODUCTION = get_date("2017-09-27")


class StatusHandler(BaseHandler):
    """Handles status states for entities in the database"""

    def samples_to_receive(self, external=False):
        """Fetch incoming samples."""
        records = (
            self.Sample.query.join(
                models.Sample.application_version, models.ApplicationVersion.application
            )
            .filter(
                models.Sample.received_at == None,
                models.Sample.downsampled_to == None,
                models.Application.is_external == external,
            )
            .order_by(models.Sample.ordered_at)
        )
        return records

    def samples_to_prepare(self):
        """Fetch samples in lab prep queue."""
        records = (
            self.Sample.query.join(
                models.Sample.application_version, models.ApplicationVersion.application
            )
            .filter(
                models.Sample.received_at != None,
                models.Sample.prepared_at == None,
                models.Sample.downsampled_to == None,
                models.Application.is_external == False,
                models.Sample.sequenced_at == None,
            )
            .order_by(models.Sample.priority.desc(), models.Sample.received_at)
        )
        return records

    def samples_to_sequence(self):
        """Fetch samples in sequencing."""
        records = (
            self.Sample.query.join(
                models.Sample.application_version, models.ApplicationVersion.application
            )
            .filter(
                models.Sample.prepared_at != None,
                models.Sample.sequenced_at == None,
                models.Sample.downsampled_to == None,
                models.Application.is_external == False,
            )
            .order_by(models.Sample.priority.desc(), models.Sample.received_at)
        )
        return records

    def cases_to_analyze(
        self, pipeline: str = "", threshold: float = None, limit: int = None
    ) -> list:
        """Returns a list if cases ready to be analyzed or set to be reanalyzed"""
        families_query = (
            self.Family.query.outerjoin(models.Analysis)
            .join(models.Family.links, models.FamilySample.sample)
            .filter(or_(models.Sample.is_external, models.Sample.sequenced_at.isnot(None)))
            .filter(models.Family.data_analysis.ilike(f"%{pipeline}%"))
            .filter(
                or_(
                    models.Family.action == "analyze",
                    and_(models.Family.action.is_(None), models.Analysis.created_at.is_(None)),
                )
            )
            .order_by(models.Family.priority.desc(), models.Family.ordered_at)
        )

        families = [
            case_obj
            for case_obj in families_query
            if self._all_samples_have_sequence_data(case_obj.links)
        ]

        if threshold:
            families = [
                case_obj
                for case_obj in families
                if self.all_samples_have_enough_reads(case_obj.links, threshold=threshold)
            ]
        return families[:limit]

    def cases_to_store(self, pipeline: str, limit: int = None) -> list:
        """Returns a list of cases that may be available to store in Housekeeper"""
        families_query = (
            self.Family.query.outerjoin(models.Analysis)
            .join(models.Family.links, models.FamilySample.sample)
            .filter(models.Family.data_analysis.ilike(f"%{pipeline}%"))
            .filter(models.Family.action == "running")
        )
        return list(families_query)[:limit]

    def get_cases_from_ticket(self, ticket_id: int) -> Query:
        records = self.Family.query.join(models.Family.links, models.FamilySample.sample).filter(
            models.Sample.ticket_number == ticket_id
        )
        return records

    def get_samples_from_ticket(self, ticket_id: int) -> List[models.Sample]:
        records = self.query(models.Sample).filter(models.Sample.ticket_number == ticket_id).all()
        return records

    def get_samples_from_flowcell(self, flowcell_id: str) -> List[models.Sample]:
        flowcell = self.query(models.Flowcell).filter(models.Flowcell.name == flowcell_id).first()
        if flowcell:
            return flowcell.samples

    def cases(
        self,
        internal_id=None,
        name=None,
        days=0,
        case_action=None,
        priority=None,
        customer_id=None,
        exclude_customer_id=None,
        data_analysis=None,
        sample_id=None,
        only_received=False,
        only_prepared=False,
        only_sequenced=False,
        only_analysed=False,
        only_uploaded=False,
        only_delivered=False,
        only_delivery_reported=False,
        only_invoiced=False,
        exclude_received=False,
        exclude_prepared=False,
        exclude_sequenced=False,
        exclude_analysed=False,
        exclude_uploaded=False,
        exclude_delivered=False,
        exclude_delivery_reported=False,
        exclude_invoiced=False,
    ):
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

        cases_sorted = sorted(cases, key=lambda k: k["tat"], reverse=True)

        return cases_sorted

    @staticmethod
    def _get_case_output(case_data: SimpleNamespace):
        case = {
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
        return case

    @staticmethod
    def _should_be_skipped(
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
    ):
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

    def _calculate_case_data(self, case_obj: models.Family):
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
                    [
                        link.sample.received_at
                        for link in case_obj.links
                        if link.sample.received_at is not None
                    ]
                )

            if case_data.samples_to_prepare > 0 and case_data.samples_prepared_bool:
                case_data.samples_prepared_at = max(
                    [
                        link.sample.prepared_at
                        for link in case_obj.links
                        if link.sample.prepared_at is not None
                    ]
                )

            if case_data.samples_to_sequence > 0 and case_data.samples_sequenced_bool:
                case_data.samples_sequenced_at = max(
                    [
                        link.sample.sequenced_at
                        for link in case_obj.links
                        if link.sample.sequenced_at is not None
                    ]
                )

            if case_data.samples_to_deliver > 0 and case_data.samples_delivered_bool:
                case_data.samples_delivered_at = max(
                    [
                        link.sample.delivered_at
                        for link in case_obj.links
                        if link.sample.delivered_at is not None
                    ]
                )

            if case_data.samples_to_invoice > 0 and case_data.samples_invoiced_bool:
                case_data.samples_invoiced_at = max(
                    [
                        link.sample.invoice.invoiced_at
                        for link in case_obj.links
                        if link.sample.invoice and link.sample.invoice.invoiced_at
                    ]
                )

            case_data.flowcells = len(
                [flowcell.status for link in case_obj.links for flowcell in link.sample.flowcells]
            )

            case_data.flowcells_status = list(
                set(
                    flowcell.status for link in case_obj.links for flowcell in link.sample.flowcells
                )
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
        case_action,
        customer_id,
        data_analysis,
        days,
        exclude_customer_id,
        internal_id,
        name,
        priority,
        sample_id,
    ):
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
            case_q = case_q.filter(models.Sample.internal_id.like(sample_id))
        else:
            case_q = case_q.outerjoin(models.Family.links, models.FamilySample.sample)
        # other joins
        case_q = case_q.outerjoin(
            models.Family.analyses, models.Sample.invoice, models.Sample.flowcells
        )
        return case_q

    @staticmethod
    def _is_rerun(case_obj, samples_received_at, samples_prepared_at, samples_sequenced_at):

        return (
            (len(case_obj.analyses) > 0)
            or (samples_received_at and samples_received_at < case_obj.ordered_at)
            or (samples_prepared_at and samples_prepared_at < case_obj.ordered_at)
            or (samples_sequenced_at and samples_sequenced_at < case_obj.ordered_at)
        )

    @staticmethod
    def _all_samples_have_sequence_data(links: List[models.FamilySample]) -> bool:
        """Return True if all samples are external or sequenced inhouse."""
        return all((link.sample.sequenced_at or link.sample.is_external) for link in links)

    def all_samples_have_enough_reads(
        self, links: List[models.FamilySample], threshold: float
    ) -> bool:
        return all(
            (
                link.sample.reads
                > self.Application.query.filter_by(
                    id=self.ApplicationVersion.query.filter_by(
                        id=link.sample.application_version_id
                    )
                    .first()
                    .application_id
                )
                .first()
                .target_reads
                * threshold
            )
            for link in links
        )

    def analyses_to_upload(self, pipeline: str = "") -> List[models.Analysis]:
        """Fetch analyses that haven't been uploaded."""
        records = self.Analysis.query.filter(
            models.Analysis.completed_at != None, models.Analysis.uploaded_at == None
        )

        if pipeline:
            records = records.filter(models.Analysis.pipeline.ilike(f"%{pipeline}%"))

        return records

    def analyses_to_clean(self, before: datetime = datetime.now(), pipeline: str = ""):
        """Fetch analyses that haven't been cleaned."""
        records = self.latest_analyses()
        records = records.filter(
            models.Analysis.uploaded_at.isnot(None),
            models.Analysis.cleaned_at.is_(None),
            models.Analysis.pipeline.ilike(f"%{pipeline}%"),
            models.Analysis.started_at <= before,
            models.Family.action == None,
        )
        return records

    def observations_to_upload(self):
        """Fetch observations that haven't been uploaded."""

        case_q = self.Family.query.join(
            models.Analysis, models.Family.links, models.FamilySample.sample
        ).filter(models.Sample.loqusdb_id.is_(None))

        return case_q

    def observations_uploaded(self):
        """Fetch observations that have been uploaded."""

        case_q = self.Family.query.join(models.Family.links, models.FamilySample.sample).filter(
            models.Sample.loqusdb_id.isnot(None)
        )

        return case_q

    def analyses_to_deliver(self, pipeline: str = ""):
        """Fetch analyses that have been uploaded but not delivered."""
        records = (
            self.Analysis.query.join(models.Family, models.Family.links, models.FamilySample.sample)
            .filter(
                models.Analysis.uploaded_at.isnot(None),
                models.Sample.delivered_at.is_(None),
                models.Analysis.pipeline.ilike(f"%{pipeline}%"),
            )
            .order_by(models.Analysis.uploaded_at.desc())
        )

        return records

    def analyses_to_delivery_report(self, pipeline: str = "") -> Query:
        """Fetch analyses that needs the delivery report to be regenerated."""

        analyses_query = self.latest_analyses()

        analyses_query = (
            analyses_query.filter(models.Analysis.uploaded_at)
            .filter(VALID_DATA_IN_PRODUCTION < models.Analysis.started_at)
            .join(models.Family, models.Family.links, models.FamilySample.sample)
            .filter(
                or_(
                    models.Family.data_analysis.is_(None),
                    models.Family.data_analysis.ilike(f"%{pipeline}%"),
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

    def samples_to_deliver(self):
        """Fetch samples that have been sequenced but not delivered."""
        records = self.Sample.query.filter(
            models.Sample.sequenced_at != None,
            models.Sample.delivered_at == None,
            models.Sample.downsampled_to == None,
        )
        return records

    def samples_not_delivered(self):
        """Fetch samples not delivered."""
        records = self.Sample.query.filter(
            models.Sample.delivered_at == None, models.Sample.downsampled_to == None
        )
        return records

    def samples_not_invoiced(self):
        """Fetch all samples that are not invoiced."""
        records = self.Sample.query.filter(
            models.Sample.downsampled_to == None, models.Sample.invoice_id == None
        )
        return records

    def samples_not_downsampled(self):
        """Fetch all samples that are not down sampled."""
        records = self.Sample.query.filter(models.Sample.downsampled_to == None)
        return records

    def microbial_samples_to_invoice(self, customer: models.Customer = None):
        """Fetch microbial samples that should be invoiced.

        Returns microbial samples that have been delivered but not invoiced.
        """
        records = self.Sample.query.filter(
            "microbial" in self.Family.data_analysis,
            models.Sample.delivered_at is not None,
            models.Sample.invoice_id == None,
        )
        customers_to_invoice = list(set([case_obj.customer for case_obj in records.all()]))
        if customer:
            records = records.join(models.Family).filter(models.Family.customer_id == customer.id)
        return records, customers_to_invoice

    def samples_to_invoice(self, customer: models.Customer = None):
        """Fetch samples that should be invoiced.

        Returns samples have been delivered but not invoiced, excluding those that
        have been marked to skip invoicing.
        """
        records = self.Sample.query.filter(
            models.Sample.delivered_at != None,
            models.Sample.invoice_id == None,
            models.Sample.no_invoice == False,
            models.Sample.downsampled_to == None,
        )
        customers_to_invoice = [
            case_obj.customer
            for case_obj in records.all()
            if not case_obj.customer.internal_id == "cust000"
        ]
        customers_to_invoice = list(set(customers_to_invoice))
        records = records.filter(models.Sample.customer == customer) if customer else records
        return records, customers_to_invoice

    def pools_to_invoice(self, customer: models.Customer = None):
        """
        Fetch pools that should be invoiced.
        """
        records = self.Pool.query.filter(
            models.Pool.invoice_id == None,
            models.Pool.no_invoice == False,
            models.Pool.delivered_at != None,
        )

        customers_to_invoice = [
            case_obj.customer
            for case_obj in records.all()
            if not case_obj.customer.internal_id == "cust000"
        ]
        customers_to_invoice = list(set(customers_to_invoice))
        records = records.filter(models.Pool.customer_id == customer.id) if customer else records
        return records, customers_to_invoice

    def pools_to_receive(self):
        """Fetch pools that have been not yet been received."""
        records = self.Pool.query.filter(models.Pool.received_at == None)
        return records

    def pools_to_deliver(self):
        """Fetch pools that have been not yet been delivered."""
        records = self.Pool.query.filter(
            models.Pool.received_at != None, models.Pool.delivered_at == None
        )
        return records

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
    ):
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
    def _calculate_date_delta(default, first_date, last_date):
        # calculates date delta between two dates, assumes last_date is today if missing
        delta = default
        if not last_date:
            last_date = datetime.now()
        if first_date:
            delta = (last_date - first_date).days
        return delta

    @staticmethod
    def _get_max_tat(links):
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
