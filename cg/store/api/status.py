# -*- coding: utf-8 -*-

from typing import List
from sqlalchemy import and_, or_

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
                models.Sample.sequenced_at == None,
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

    def families_to_analyze(self, limit: int=50):
        """Fetch families without analyses where all samples are sequenced."""
        records = (
            self.Family.query
            .outerjoin(models.Family.analyses)
            .join(models.Family.links, models.FamilySample.sample)
            .filter(
                or_(
                    models.Family.action == 'analyze',
                    and_(
                        models.Sample.sequenced_at != None,
                        models.Analysis.completed_at == None,
                        models.Family.action == None,
                    )
            ))
            .order_by(models.Family.priority.desc(), models.Family.ordered_at)
        )
        return [record for record in records.limit(limit) if self._samples_sequenced(record.links)]

    @staticmethod
    def _samples_sequenced(links: List[models.FamilySample]) -> bool:
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

    def samples_to_invoice(self, customer: models.Customer=None):
        """Fetch samples that should be invoiced.
        
        Return samples have been delivered but invoiced, excluding those that
        have been marked to skip invoicing.
        """
        records = (
            self.Sample.query
            .filter(
                models.Sample.invoice_id == None,
                models.Sample.no_invoice != True,
                models.Sample.delivered_at != True,
                models.Sample.downsampled_to == None
            )
        )
        records = records.filter(models.Sample.customer == customer) if customer else records
        return records
