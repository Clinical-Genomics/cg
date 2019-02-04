# -*- coding: utf-8 -*-
from datetime import datetime, timedelta
from typing import List
from sqlalchemy import or_, and_

from cg.constants import PRIORITY_MAP
from cg.store import models


class StatusHandler:

    def samples_to_recieve(self, external=False):
        """Fetch incoming samples."""
        records = (
            self.Sample.query
            .join(
                models.Sample.application_version,
                models.ApplicationVersion.application,
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
            self.Sample.query
            .join(
                models.Sample.application_version,
                models.ApplicationVersion.application,
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
            self.Sample.query
            .join(
                models.Sample.application_version,
                models.ApplicationVersion.application,
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

    def families_to_mip_analyze(self, limit: int = 50):
        """Fetch families without analyses where all samples are sequenced."""

        # there are two cases when a sample should be analysed:
        families_q = (
            self.Family.query
            .outerjoin(models.Analysis)
            .join(models.Family.links, models.FamilySample.sample)
            # the samples must always be sequenced to be analysed
            .filter(
                models.Sample.sequenced_at.isnot(None),
            )
            # The data_analysis is unset or not Balsamic only
            .filter(
                or_(
                    models.Sample.data_analysis.is_(None),
                    models.Sample.data_analysis != 'Balsamic'
                )
            )
            # 1. family that has been analysed but now is requested for re-analysing
            # 2. new family with that haven't been analysed
            .filter(
                or_(
                    models.Family.action == 'analyze',
                    and_(
                        models.Family.action.is_(None),
                        models.Analysis.created_at.is_(None),
                    ),
                )
            )
            .order_by(models.Family.priority.desc(), models.Family.ordered_at)
        )

        families = [record for record in families_q if self._all_samples_sequenced(record.links)]

        return families[:limit]

    def active_cases(self,
                     internal_id=None,
                     name=None,
                     days=31,
                     action=None,
                     priority=None,
                     customer_id=None,
                     exclude_customer_id=None,
                     data_analysis=None,
                     sample_id = None,
                     exclude_received=False,
                     exclude_prepared=False,
                     exclude_sequenced=False,
                     exclude_analysed=False,
                     exclude_uploaded=False,
                     exclude_delivered=False,
                     exclude_invoiced=False,
                     ):
        """Fetch cases with and w/o analyses"""
        families_q = self.Family.query

        # family filters
        if days != 0:
            filter_date = datetime.now() - timedelta(days=days)
            families_q = families_q.filter(models.Family.ordered_at > filter_date)

        if action:
            families_q = families_q.filter(models.Family.action == action)

        if priority:
            priority_db = PRIORITY_MAP[priority]
            families_q = families_q.filter(models.Family.priority == priority_db)

        if internal_id:
            families_q = families_q.filter(models.Family.internal_id.like('%' + internal_id + '%'))

        if name:
            families_q = families_q.filter(models.Family.name.like('%' + name + '%'))

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
                families_q = families_q.filter(models.Sample.data_analysis.like('%' +
                                                                                data_analysis +
                                                                                '%'))
            if sample_id:
                families_q = families_q.filter(models.Sample.internal_id.like(sample_id))

        else:
            families_q = families_q.outerjoin(models.Family.links, models.FamilySample.sample)

        # other joins
        families_q = families_q.outerjoin(models.Family.analyses, models.Sample.invoice)

        families_q = families_q.order_by(models.Family.ordered_at.desc())

        cases = []

        for record in families_q:

            samples_received = None
            samples_prepared = None
            samples_sequenced = None
            samples_invoiced = None
            samples_received_bool = None
            samples_prepared_bool = None
            samples_sequenced_bool = None
            samples_invoiced_bool = None
            analysis_completed = None
            analysis_uploaded = None
            samples_delivered = None
            analysis_pipeline = None
            analysis_completed_bool = None
            analysis_uploaded_bool = None
            samples_delivered_bool = None
            samples_data_analyses = None

            total_samples = len(record.links)
            total_external_samples = len([link.sample.is_external for link in record.links if
                                    link.sample.is_external])
            total_internal_samples = total_samples - total_external_samples

            if total_samples > 0:
                samples_received = len([link.sample.received_at for link in record.links if
                                        link.sample.received_at is not None])
                samples_prepared = len([link.sample.prepared_at for link in record.links if
                                        link.sample.prepared_at is not None])
                samples_sequenced = len([link.sample.sequenced_at for link in record.links if
                                         link.sample.sequenced_at is not None])
                samples_delivered = len([link.sample.delivered_at for link in record.links if
                                         link.sample.delivered_at is not None])
                samples_invoiced = len([link.sample.invoice.invoiced_at for link in record.links if
                                        link.sample.invoice is not None])
                samples_received_bool = samples_received == total_internal_samples
                samples_prepared_bool = samples_prepared == total_internal_samples
                samples_delivered_bool = samples_delivered == total_samples
                samples_sequenced_bool = samples_sequenced == total_samples
                samples_invoiced_bool = samples_invoiced == total_samples
                samples_data_analyses = set(link.sample.data_analysis for link in record.links)

            if record.analyses:
                analysis_completed = record.analyses[0].completed_at
                analysis_uploaded = record.analyses[0].uploaded_at
                analysis_pipeline = record.analyses[0].pipeline
                analysis_completed_bool = analysis_completed is not None
                analysis_uploaded_bool = analysis_uploaded is not None
            elif total_samples > 0:
                analysis_completed_bool = False
                analysis_uploaded_bool = False

            case = {
                'internal_id': record.internal_id,
                'name': record.name,
                'ordered_at': record.ordered_at,
                'total_samples': total_samples,
                'total_external_samples': total_external_samples,
                'total_internal_samples': total_internal_samples,
                'samples_data_analyses': samples_data_analyses,
                'samples_received': samples_received,
                'samples_prepared': samples_prepared,
                'samples_sequenced': samples_sequenced,
                'analysis_completed_at': analysis_completed,
                'analysis_uploaded_at': analysis_uploaded,
                'samples_delivered': samples_delivered,
                'samples_invoiced': samples_invoiced,
                'analysis_pipeline': analysis_pipeline,
                'samples_received_bool': samples_received_bool,
                'samples_prepared_bool': samples_prepared_bool,
                'samples_sequenced_bool': samples_sequenced_bool,
                'analysis_completed_bool': analysis_completed_bool,
                'analysis_uploaded_bool': analysis_uploaded_bool,
                'samples_delivered_bool': samples_delivered_bool,
                'samples_invoiced_bool': samples_invoiced_bool,
            }

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

            if exclude_invoiced and samples_invoiced_bool:
                continue

            cases.append(case)

        return cases

    @staticmethod
    def _all_samples_sequenced(links: List[models.FamilySample]) -> bool:
        """Return True if all samples are sequenced."""
        return all(link.sample.sequenced_at for link in links)

    def analyses_to_upload(self):
        """Fetch analyses that haven't been uploaded."""
        records = self.Analysis.query.filter(models.Analysis.completed_at != None,
                                             models.Analysis.uploaded_at == None)
        return records

    def analyses_to_deliver(self):
        """Fetch analyses that have been uploaded but not delivered."""
        records = (
            self.Analysis.query
            .filter(
                models.Analysis.uploaded_at != None,
                models.Analysis.delivered_at == None
            )
            .order_by(models.Analysis.uploaded_at.desc())
        )
        return records

    def samples_to_deliver(self):
        """Fetch samples that have been sequenced but not delivered."""
        records = (
            self.Sample.query
            .filter(
                models.Sample.sequenced_at != None,
                models.Sample.delivered_at == None,
                models.Sample.downsampled_to == None
            )
        )
        return records

    def samples_not_delivered(self):
        """Fetch samples not delivered."""
        records = (
            self.Sample.query
            .filter(
                models.Sample.delivered_at == None,
                models.Sample.downsampled_to == None
            )
        )
        return records

    def samples_not_invoiced(self):
        """Fetch all samples that are not invoiced."""
        records = (
            self.Sample.query
            .filter(
                models.Sample.downsampled_to == None,
                models.Sample.invoice_id == None,
            )
        )
        return records

    def samples_not_downsampled(self):
        """Fetch all samples that are not down sampled."""
        records = (
            self.Sample.query
            .filter(
                models.Sample.downsampled_to == None
            )
        )
        return records

    def samples_to_invoice(self, customer: models.Customer = None):
        """Fetch samples that should be invoiced.

        Return samples have been delivered but invoiced, excluding those that
        have been marked to skip invoicing.
        """
        records = (
            self.Sample.query.filter(
                models.Sample.delivered_at != None,
                models.Sample.invoice_id == None,
                models.Sample.no_invoice == False,
                models.Sample.downsampled_to == None
            )
        )
        customers_to_invoice = [record.customer for record in records.all() if
                                not record.customer.internal_id == 'cust000']
        customers_to_invoice = list(set(customers_to_invoice))
        records = records.filter(models.Sample.customer == customer) if customer else records
        return records, customers_to_invoice

    def pools_to_invoice(self, customer: models.Customer = None):
        """
        Fetch pools that should be invoiced.
        """
        records = (
            self.Pool.query.filter(
                models.Pool.invoice_id == None,
                models.Pool.no_invoice == False,
                models.Pool.delivered_at != None
            )
        )

        customers_to_invoice = [record.customer for record in records.all() if
                                not record.customer.internal_id == 'cust000']
        customers_to_invoice = list(set(customers_to_invoice))
        records = records.filter(models.Pool.customer_id == customer.id) if customer else records
        return records, customers_to_invoice

    def pools_to_receive(self):
        """Fetch pools that have been not yet been received."""
        records = (
            self.Pool.query
            .filter(
                models.Pool.received_at == None
            )
        )
        return records

    def pools_to_deliver(self):
        """Fetch pools that have been not yet been delivered."""
        records = (
            self.Pool.query
            .filter(
                models.Pool.received_at != None,
                models.Pool.delivered_at == None
            )
        )
        return records

    def microbial_samples_to_receive(self, external=False):
        """Fetch microbial samples from statusdb that have no received_at date."""
        records = (
            self.MicrobialSample.query
            .join(
                models.MicrobialSample.application_version,
                models.ApplicationVersion.application,
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
            self.MicrobialSample.query
            .join(
                models.MicrobialSample.application_version,
                models.ApplicationVersion.application,
            )
            .filter(
                models.MicrobialSample.prepared_at == None,
                models.Application.is_external == external,
            )
            .order_by(models.MicrobialSample.created_at)
        )
        return records

    def microbial_samples_to_sequence(self, external=False):
        """Fetch microbial samples from statusdb that have no sequenced_at date."""
        records = (
            self.MicrobialSample.query
            .join(
                models.MicrobialSample.application_version,
                models.ApplicationVersion.application,
            )
            .filter(
                models.MicrobialSample.sequenced_at == None,
                models.Application.is_external == external,
            )
            .order_by(models.MicrobialSample.created_at)
        )
        return records

    def microbial_samples_to_deliver(self, external=False):
        """Fetch microbial samples from statusdb that have no delivered_at date."""
        records = (
            self.MicrobialSample.query
            .join(
                models.MicrobialSample.application_version,
                models.ApplicationVersion.application,
            )
            .filter(
                models.MicrobialSample.delivered_at == None,
                models.Application.is_external == external,
            )
            .order_by(models.MicrobialSample.created_at)
        )
        return records
