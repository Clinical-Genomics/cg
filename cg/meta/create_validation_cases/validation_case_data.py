"""Model for down sampling meta data."""

import logging
from pathlib import Path

from cg.apps.housekeeper.hk import HousekeeperAPI
from cg.constants import DataDelivery, Priority
from cg.constants.constants import CaseActions, CustomerId
from cg.meta.create_validation_cases.validation_data_input import ValidationDataInput
from cg.store.models import ApplicationVersion, Case, Sample, Customer
from cg.store.store import Store
from cg.utils.calculations import multiply_by_million

LOG = logging.getLogger(__name__)


class ValidationCaseData:
    def __init__(self, status_db: Store, validation_data_input: ValidationDataInput):
        """Initialize the validation sample data and perform integrity checks."""
        self.status_db: Store = status_db
        self.input_data: ValidationDataInput = validation_data_input
        self.case_id: str = validation_data_input.case_id
        self.case_name: str = validation_data_input.case_name
        self.original_case: Case = self.get_case_to_copy()
        self.original_samples: list[Sample] = self.get_samples_to_copy()
        self.validation_samples: list[Sample] = self.get_validation_samples()
        self.validation_case: Case = self._generate_validation_case()
        LOG.info(f"Validation Data checks completed for {self.case_id}")

    @staticmethod
    def _validation_sample_id(sample: Sample) -> str:
        """Return a new validation sample identifier. The identifier removes "ACC" and prepends "VAL"."""
        return "VAL" + sample.internal_id[3:]

    @property
    def validation_case_name(
        self,
    ) -> str:
        """Return a case name with _validation appended."""
        return f"{self.case_name}_validation"

    def get_samples_to_copy(self) -> list[Sample]:
        """
        Return samples associated to a case.
        """
        case: Case = self.status_db.get_case_by_internal_id(self.case_id)
        return [sample for sample in case.samples]

    def get_case_to_copy(self) -> Case:
        """
        Check if a case exists in StatusDB.
            Raises: ValueError
        """
        case: Case = self.status_db.get_case_by_internal_id(self.case_id)
        if not case:
            raise ValueError(f"Case {self.case_id} not found in StatusDB.")
        return case

    def _generate_validation_samples(
        self,
        original_sample: Sample,
    ) -> Sample:
        """
        Generate a validation sample record for StatusDB.
        The new sample contains the original sample internal id and meta data
        """
        application_version: ApplicationVersion = self._get_application_version(original_sample)
        sample_id: str = self._validation_sample_id(original_sample)
        customer_id: int = self.status_db.get_customer_by_internal_id(
            CustomerId.CG_INTERNAL_CUSTOMER.value
        ).id
        validation_sample: Sample = self.status_db.add_sample(
            name=sample_id,
            internal_id=sample_id,
            sex=original_sample.sex,
            order=original_sample.order,
            from_sample=original_sample.internal_id,
            tumour=original_sample.is_tumour,
            priority=Priority.standard,
            customer_id=customer_id,
            application_version=application_version,
            received=original_sample.received_at,
            prepared_at=original_sample.prepared_at,
            last_sequenced_at=original_sample.last_sequenced_at,
        )
        return validation_sample

    def get_validation_samples(self):
        return [self._generate_validation_samples(sample) for sample in self.original_samples]

    def _generate_validation_case(
        self,
    ) -> Case:
        """
        Generate a case for the validation samples.
        The new case uses existing case data.
        Customer will be set to cust000.
        """
        if self.status_db.case_with_name_exists(case_name=self.validation_case_name):
            raise ValueError(f"Case with name {self.case_name} already exists.")
        validation_case: Case = self.status_db.add_case(
            data_analysis=(self.input_data.data_analysis or self.original_case.data_analysis),
            data_delivery=(self.input_data.delivery or self.original_case.data_delivery),
            name=self.validation_case_name,
            panels=self.original_case.panels,
            priority=Priority.standard,
            ticket=self.original_case.latest_ticket,
        )
        validation_case.orders.append(self.original_case.latest_order)
        customer: Customer = self.status_db.get_customer_by_internal_id(
            CustomerId.CG_INTERNAL_CUSTOMER
        )
        validation_case.customer = customer
        validation_case.is_compressible = False
        validation_case.action = CaseActions.HOLD
        return validation_case

    @staticmethod
    def _get_application_version(sample: Sample) -> ApplicationVersion:
        """Return the application version for a sample."""
        return sample.application_version
