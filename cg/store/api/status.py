from datetime import datetime, timedelta
from typing import List

from cg.constants import PRIORITY_MAP
from cg.store import models
from cg.store.api.base import BaseHandler
from cg.utils.date import get_date
from sqlalchemy import or_, and_, func
from sqlalchemy.orm import Query

HASTA_IN_PRODUCTION = get_date("2017-09-27")


class StatusHandler(BaseHandler):
    """Handles status states for entities in the database"""

    def samples_to_recieve(self, external=False):
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
            .filter(models.Sample.data_analysis.ilike(f"%{pipeline}%"))
            .filter(
                or_(
                    models.Family.action == "analyze",
                    and_(models.Family.action.is_(None), models.Analysis.created_at.is_(None)),
                )
            )
            .order_by(models.Family.priority.desc(), models.Family.ordered_at)
        )

        families = [
            record
            for record in families_query
            if self._all_samples_have_sequence_data(record.links)
        ]

        if threshold:
            families = [
                record
                for record in families
                if self.all_samples_have_enough_reads(record.links, threshold=threshold)
            ]
        return families[:limit]

    def cases_to_store(self, pipeline: str, limit: int = None) -> list:
        """Returns a list of cases that may be available to store in Housekeeper"""
        families_query = (
            self.Family.query.outerjoin(models.Analysis)
            .join(models.Family.links, models.FamilySample.sample)
            .filter(or_(models.Sample.is_external, models.Sample.sequenced_at.isnot(None)))
            .filter(models.Sample.data_analysis.ilike(f"%{pipeline}%"))
            .filter(models.Family.action == "running")
            .order_by(models.Family.priority.desc(), models.Family.ordered_at)
        )
        return list(families_query)[:limit]

    def cases(
        self,
        progress_tracker=None,
        internal_id=None,
        name=None,
        days=0,
        case_action=None,
        progress_status=None,
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
        families_q = self.Family.query

        # family filters
        if days != 0:
            filter_date = datetime.now() - timedelta(days=days)
            families_q = families_q.filter(models.Family.ordered_at > filter_date)

        if case_action:
            families_q = families_q.filter(models.Family.action == case_action)

        if priority:
            priority_db = PRIORITY_MAP[priority]
            families_q = families_q.filter(models.Family.priority == priority_db)

        if internal_id:
            families_q = families_q.filter(models.Family.internal_id.like("%" + internal_id + "%"))

        if name:
            families_q = families_q.filter(models.Family.name.like("%" + name + "%"))

        # customer filters
        if customer_id or exclude_customer_id:
            families_q = families_q.join(models.Family.customer)

            if customer_id:
                families_q = families_q.filter(models.Customer.internal_id == customer_id)

            if exclude_customer_id:
                families_q = families_q.filter(models.Customer.internal_id != exclude_customer_id)

        # sample filters
        if data_analysis or sample_id:
            families_q = families_q.join(models.Family.links, models.FamilySample.sample)
            if data_analysis:
                families_q = families_q.filter(
                    models.Sample.data_analysis.like("%" + data_analysis + "%")
                )
            if sample_id:
                families_q = families_q.filter(models.Sample.internal_id.like(sample_id))

        else:
            families_q = families_q.outerjoin(models.Family.links, models.FamilySample.sample)

        # other joins
        families_q = families_q.outerjoin(
            models.Family.analyses, models.Sample.invoice, models.Sample.flowcells
        )

        cases = []

        for record in families_q:

            samples_received = None
            samples_prepared = None
            samples_sequenced = None
            samples_delivered = None
            samples_invoiced = None
            samples_received_at = None
            samples_prepared_at = None
            samples_sequenced_at = None
            samples_delivered_at = None
            samples_invoiced_at = None
            samples_to_receive = None
            samples_to_prepare = None
            samples_to_sequence = None
            samples_to_deliver = None
            samples_to_invoice = None
            samples_received_bool = None
            samples_prepared_bool = None
            samples_sequenced_bool = None
            samples_invoiced_bool = None
            analysis_completed_at = None
            analysis_uploaded_at = None
            analysis_delivery_reported_at = None
            analysis_pipeline = None
            analysis_status = None
            analysis_completion = None
            analysis_completed_bool = None
            analysis_uploaded_bool = None
            samples_delivered_bool = None
            analysis_delivery_reported_bool = None
            samples_data_analyses = None
            flowcells_status = None
            flowcells_on_disk = None
            flowcells_on_disk_bool = None
            tat = None
            is_rerun = False

            analysis_in_progress = record.action is not None
            case_action = record.action

            total_samples = len(record.links)
            total_external_samples = len(
                [
                    link.sample.application_version.application.is_external
                    for link in record.links
                    if link.sample.application_version.application.is_external
                ]
            )
            total_internal_samples = total_samples - total_external_samples
            case_external_bool = total_external_samples == total_samples

            if total_samples > 0:
                samples_received = len(
                    [
                        link.sample.received_at
                        for link in record.links
                        if link.sample.received_at is not None
                    ]
                )
                samples_prepared = len(
                    [
                        link.sample.prepared_at
                        for link in record.links
                        if link.sample.prepared_at is not None
                    ]
                )
                samples_sequenced = len(
                    [
                        link.sample.sequenced_at
                        for link in record.links
                        if link.sample.sequenced_at is not None
                    ]
                )
                samples_delivered = len(
                    [
                        link.sample.delivered_at
                        for link in record.links
                        if link.sample.delivered_at is not None
                    ]
                )
                samples_invoiced = len(
                    [
                        link.sample.invoice.invoiced_at
                        for link in record.links
                        if link.sample.invoice and link.sample.invoice.invoiced_at
                    ]
                )

                samples_to_receive = total_internal_samples
                samples_to_prepare = total_internal_samples
                samples_to_sequence = total_internal_samples
                samples_to_deliver = total_internal_samples
                samples_to_invoice = total_samples - len(
                    [link.sample.no_invoice for link in record.links if link.sample.no_invoice]
                )

                samples_received_bool = samples_received == samples_to_receive
                samples_prepared_bool = samples_prepared == samples_to_prepare
                samples_sequenced_bool = samples_sequenced == samples_to_sequence
                samples_delivered_bool = samples_delivered == samples_to_deliver
                samples_invoiced_bool = samples_invoiced == samples_to_invoice
                samples_data_analyses = list(
                    set(link.sample.data_analysis for link in record.links)
                )

                if samples_to_receive > 0 and samples_received_bool:
                    samples_received_at = max(
                        [
                            link.sample.received_at
                            for link in record.links
                            if link.sample.received_at is not None
                        ]
                    )

                if samples_to_prepare > 0 and samples_prepared_bool:
                    samples_prepared_at = max(
                        [
                            link.sample.prepared_at
                            for link in record.links
                            if link.sample.prepared_at is not None
                        ]
                    )

                if samples_to_sequence > 0 and samples_sequenced_bool:
                    samples_sequenced_at = max(
                        [
                            link.sample.sequenced_at
                            for link in record.links
                            if link.sample.sequenced_at is not None
                        ]
                    )

                if samples_to_deliver > 0 and samples_delivered_bool:
                    samples_delivered_at = max(
                        [
                            link.sample.delivered_at
                            for link in record.links
                            if link.sample.delivered_at is not None
                        ]
                    )

                if samples_to_invoice > 0 and samples_invoiced_bool:
                    samples_invoiced_at = max(
                        [
                            link.sample.invoice.invoiced_at
                            for link in record.links
                            if link.sample.invoice and link.sample.invoice.invoiced_at
                        ]
                    )

                flowcells = len(
                    [flowcell.status for link in record.links for flowcell in link.sample.flowcells]
                )

                flowcells_status = list(
                    set(
                        flowcell.status
                        for link in record.links
                        for flowcell in link.sample.flowcells
                    )
                )
                if flowcells < total_samples:
                    flowcells_status.append("new")

                flowcells_status = ", ".join(flowcells_status)

                flowcells_on_disk = len(
                    [
                        flowcell.status
                        for link in record.links
                        for flowcell in link.sample.flowcells
                        if flowcell.status == "ondisk"
                    ]
                )

                flowcells_on_disk_bool = flowcells_on_disk == total_samples

            if record.analyses and not analysis_in_progress:
                analysis_completed_at = record.analyses[0].completed_at
                analysis_uploaded_at = record.analyses[0].uploaded_at
                analysis_delivery_reported_at = record.analyses[0].delivery_report_created_at
                analysis_pipeline = record.analyses[0].pipeline
                analysis_completed_bool = analysis_completed_at is not None
                analysis_uploaded_bool = analysis_uploaded_at is not None
                analysis_delivery_reported_bool = analysis_delivery_reported_at is not None
            elif total_samples > 0:
                analysis_completed_bool = False
                analysis_uploaded_bool = False
                analysis_delivery_reported_bool = False

            if only_received and not samples_received_bool:
                continue

            if only_prepared and not samples_prepared_bool:
                continue

            if only_sequenced and not samples_sequenced_bool:
                continue

            if only_analysed and not analysis_completed_bool:
                continue

            if only_uploaded and not analysis_uploaded_bool:
                continue

            if only_delivered and not samples_delivered_bool:
                continue

            if only_delivery_reported and not analysis_delivery_reported_bool:
                continue

            if only_invoiced and not samples_invoiced_bool:
                continue

            if exclude_received and samples_received_bool:
                continue

            if exclude_prepared and samples_prepared_bool:
                continue

            if exclude_sequenced and samples_sequenced_bool:
                continue

            if exclude_analysed and analysis_completed_bool:
                continue

            if exclude_uploaded and analysis_uploaded_bool:
                continue

            if exclude_delivered and samples_delivered_bool:
                continue

            if exclude_delivery_reported and analysis_delivery_reported_bool:
                continue

            if exclude_invoiced and samples_invoiced_bool:
                continue

            if progress_tracker:
                for analysis_obj in progress_tracker.get_latest_logged_analysis(
                    case_id=record.internal_id
                ):

                    if not analysis_status:
                        analysis_completion = round(analysis_obj.progress * 100)
                        analysis_status = analysis_obj.status

            # filter on a status
            if progress_status and progress_status != analysis_status:
                continue

            is_rerun = self._is_rerun(
                record, samples_received_at, samples_prepared_at, samples_sequenced_at
            )

            tat = self._calculate_estimated_turnaround_time(
                is_rerun,
                case_external_bool,
                record.ordered_at,
                samples_received_at,
                samples_prepared_at,
                samples_sequenced_at,
                analysis_completed_at,
                analysis_uploaded_at,
                samples_delivered_at,
            )

            max_tat = self._get_max_tat(links=record.links)

            case = {
                "internal_id": record.internal_id,
                "name": record.name,
                "ordered_at": record.ordered_at,
                "total_samples": total_samples,
                "total_external_samples": total_external_samples,
                "total_internal_samples": total_internal_samples,
                "case_external_bool": case_external_bool,
                "samples_to_receive": samples_to_receive,
                "samples_to_prepare": samples_to_prepare,
                "samples_to_sequence": samples_to_sequence,
                "samples_to_deliver": samples_to_deliver,
                "samples_to_invoice": samples_to_invoice,
                "samples_data_analyses": samples_data_analyses,
                "samples_received": samples_received,
                "samples_prepared": samples_prepared,
                "samples_sequenced": samples_sequenced,
                "samples_received_at": samples_received_at,
                "samples_prepared_at": samples_prepared_at,
                "samples_sequenced_at": samples_sequenced_at,
                "samples_delivered_at": samples_delivered_at,
                "samples_invoiced_at": samples_invoiced_at,
                "case_action": case_action,
                "analysis_status": analysis_status,
                "analysis_completion": analysis_completion,
                "analysis_completed_at": analysis_completed_at,
                "analysis_uploaded_at": analysis_uploaded_at,
                "samples_delivered": samples_delivered,
                "analysis_delivery_reported_at": analysis_delivery_reported_at,
                "samples_invoiced": samples_invoiced,
                "analysis_pipeline": analysis_pipeline,
                "samples_received_bool": samples_received_bool,
                "samples_prepared_bool": samples_prepared_bool,
                "samples_sequenced_bool": samples_sequenced_bool,
                "analysis_completed_bool": analysis_completed_bool,
                "analysis_uploaded_bool": analysis_uploaded_bool,
                "samples_delivered_bool": samples_delivered_bool,
                "analysis_delivery_reported_bool": analysis_delivery_reported_bool,
                "samples_invoiced_bool": samples_invoiced_bool,
                "flowcells_status": flowcells_status,
                "flowcells_on_disk": flowcells_on_disk,
                "flowcells_on_disk_bool": flowcells_on_disk_bool,
                "tat": tat,
                "is_rerun": is_rerun,
                "max_tat": max_tat,
            }

            cases.append(case)

        cases_sorted = sorted(cases, key=lambda k: k["tat"], reverse=True)

        return cases_sorted

    @staticmethod
    def _is_rerun(record, samples_received_at, samples_prepared_at, samples_sequenced_at):

        return (
            (len(record.analyses) > 0)
            or (samples_received_at and samples_received_at < record.ordered_at)
            or (samples_prepared_at and samples_prepared_at < record.ordered_at)
            or (samples_sequenced_at and samples_sequenced_at < record.ordered_at)
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

    def analyses_to_clean(self, pipeline: str = ""):
        """Fetch analyses that haven't been cleaned."""
        records = self.latest_analyses()
        records = records.filter(
            models.Analysis.uploaded_at.isnot(None),
            models.Analysis.cleaned_at.is_(None),
            models.Analysis.pipeline.ilike(f"%{pipeline}%"),
        )
        return records

    def observations_to_upload(self):
        """Fetch observations that haven't been uploaded."""

        families_q = self.Family.query.join(
            models.Analysis, models.Family.links, models.FamilySample.sample
        ).filter(models.Sample.loqusdb_id.is_(None))

        return families_q

    def observations_uploaded(self):
        """Fetch observations that have been uploaded."""

        families_q = self.Family.query.join(models.Family.links, models.FamilySample.sample).filter(
            models.Sample.loqusdb_id.isnot(None)
        )

        return families_q

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
            .filter(HASTA_IN_PRODUCTION < models.Analysis.started_at)
            .join(models.Family, models.Family.links, models.FamilySample.sample)
            .filter(
                or_(
                    models.Sample.data_analysis.is_(None),
                    models.Sample.data_analysis.ilike(f"%{pipeline}%"),
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
            "microbial" in self.Sample.data_analysis,
            models.Sample.delivered_at is not None,
            models.Sample.invoice_id == None,
        )
        customers_to_invoice = list(set([record.customer for record in records.all()]))
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
            record.customer
            for record in records.all()
            if not record.customer.internal_id == "cust000"
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
            record.customer
            for record in records.all()
            if not record.customer.internal_id == "cust000"
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

    def microbial_samples_to_receive(self, external=False):
        """Fetch microbial samples from statusdb that have no received_at date."""
        records = (
            self.MicrobialSample.query.join(
                models.MicrobialSample.application_version, models.ApplicationVersion.application
            )
            .filter(
                models.MicrobialSample.received_at == None,
                models.Application.is_external == external,
            )
            .order_by(models.MicrobialSample.created_at)
        )
        return records

    def microbial_samples_to_prepare(self, external=False):
        """Fetch microbial samples from statusdb that have no prepared_at date."""
        records = (
            self.Sample.query.join(
                models.Sample.application_version, models.ApplicationVersion.application
            )
            .filter(
                "microbial" in self.Sample.data_analysis,
                models.Sample.prepared_at == None,
                models.Application.is_external == external,
            )
            .order_by(models.Sample.created_at)
        )
        return records

    def microbial_samples_to_sequence(self, external=False):
        """Fetch microbial samples from statusdb that have no sequenced_at date."""
        records = (
            self.Sample.query.join(
                models.Sample.application_version, models.ApplicationVersion.application
            )
            .filter(
                "microbial" in self.Sample.data_analysis,
                models.Sample.sequenced_at == None,
                models.Application.is_external == external,
            )
            .order_by(models.Sample.created_at)
        )
        return records

    def microbial_samples_to_deliver(self, external=False):
        """Fetch microbial samples from statusdb that have no delivered_at date."""
        records = (
            self.Sample.query.join(
                models.Sample.application_version, models.ApplicationVersion.application
            )
            .filter(
                "microbial" in self.Sample.data_analysis,
                models.Sample.delivered_at == None,
                models.Application.is_external == external,
            )
            .order_by(models.Sample.created_at)
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
