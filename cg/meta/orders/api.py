# -*- coding: utf-8 -*-
import logging
from enum import Enum
from typing import List

from cg.apps.lims import LimsAPI
from cg.apps.osticket import OsTicket
from cg.exc import OrderError, TicketCreationError
from cg.store import Store
from .schema import ExternalProject, FastqProject, RmlProject, ScoutProject
from .lims import LimsHandler
from .status import StatusHandler

LOG = logging.getLogger(__name__)


class OrderType(Enum):
    EXTERNAL = 'external'
    FASTQ = 'fastq'
    RML = 'rml'
    SCOUT = 'scout'


class OrdersAPI(LimsHandler, StatusHandler):

    """Orders API for accepting new samples into the system."""

    types = {
        OrderType.EXTERNAL: ExternalProject(),
        OrderType.FASTQ: FastqProject(),
        OrderType.RML: RmlProject(),
        OrderType.SCOUT: ScoutProject()
    }

    def __init__(self, lims: LimsAPI, status: Store, osticket: OsTicket):
        self.lims = lims
        self.status = status
        self.osticket = osticket

    def submit(self, project: OrderType, name: str, email: str, data: dict) -> dict:
        """Submit a batch of samples."""
        errors = self.types[project].validate(data)
        if errors:
            return errors
        message = f"New incoming samples, {name}"
        try:
            data['ticket'] = (self.osticket.open_ticket(name, email, subject=data['name'],
                                                        message=message)
                              if self.osticket else None)
        except TicketCreationError as error:
            LOG.warning(error.message)
            data['ticket'] = None
        result = getattr(self, f"submit_{project.value}")(data)
        return result

    def submit_rml(self, data: dict) -> dict:
        """Submit a batch of ready made libraries."""
        status_data = self.pools_to_status(data)
        project_data, _ = self.process_lims(data)
        new_records = self.store_pools(
            customer=status_data['customer'],
            order=status_data['order'],
            ordered=project_data['date'],
            ticket=data['ticket'],
            pools=status_data['pools'],
        )
        return {'project': project_data, 'records': new_records}

    def submit_fastq(self, data: dict) -> dict:
        """Submit a batch of samples for FASTQ delivery."""
        status_data = self.samples_to_status(data)
        project_data, lims_map = self.process_lims(data)
        self.fillin_sample_ids(status_data['samples'], lims_map)
        new_records = self.store_samples(
            customer=status_data['customer'],
            order=status_data['order'],
            ordered=project_data['date'],
            ticket=data['ticket'],
            samples=status_data['samples'],
        )
        return {'project': project_data, 'records': new_records}

    def submit_external(self, data: dict) -> dict:
        """Submit a batch of externally sequenced samples for analysis."""
        result = self.process_analysis_samples(data)
        return result

    def submit_scout(self, data: dict) -> dict:
        """Submit a batch of samples for sequencing and analysis."""
        result = self.process_analysis_samples(data)
        return result

    def process_analysis_samples(self, data: dict) -> dict:
        """Process samples to be analyzed."""
        status_data = self.families_to_status(data)
        customer_obj = self.status.customer(status_data['customer'])
        for family in status_data['families']:
            family_obj = self.status.find_family(customer_obj, family['name'])
            if family_obj:
                raise OrderError(f"family name already used: {family_obj.name}")

        project_data, lims_map = self.process_lims(data)
        samples = [sample
                   for family in status_data['families']
                   for sample in family['samples']]
        self.fillin_sample_ids(samples, lims_map)
        new_families = self.store_families(
            customer=status_data['customer'],
            order=status_data['order'],
            ordered=project_data['date'],
            ticket=data['ticket'],
            families=status_data['families'],
        )
        return {'project': project_data, 'records': new_families}

    def fillin_sample_ids(self, samples: List[dict], lims_map: dict):
        """Fill in LIMS sample ids."""
        for sample in samples:
            sample['internal_id'] = lims_map.get(sample['name']) or sample['internal_id']
