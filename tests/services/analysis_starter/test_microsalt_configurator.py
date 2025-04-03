from pathlib import Path
from unittest import mock

import pytest

from cg.constants import DataDelivery, FileExtensions, Priority, Workflow
from cg.exc import CaseNotConfiguredError, CgDataError
from cg.io.controller import WriteFile
from cg.meta.workflow.fastq import FastqHandler
from cg.models.orders.sample_base import SexEnum, StatusEnum
from cg.services.analysis_starter.configurator.implementations.microsalt import (
    MicrosaltConfigurator,
)
from cg.services.analysis_starter.configurator.models.microsalt import MicrosaltCaseConfig
from cg.store.models import Application, Case, Customer, Organism, Sample


@pytest.fixture(autouse=True)
def mock_file_creation():
    """Mocks run before each test in the module."""
    with (
        mock.patch.object(FastqHandler, "link_fastq_files_for_sample", return_value=None),
        mock.patch.object(WriteFile, "write_file_from_content", return_value=None),
    ):
        yield


def test_configure_success(microsalt_configurator: MicrosaltConfigurator):
    # GIVEN a microSALT configurator

    # GIVEN a microSALT case
    microsalt_case: Case = microsalt_configurator.store.add_case(
        customer_id=0,
        data_analysis=Workflow.MICROSALT,
        data_delivery=DataDelivery.ANALYSIS_FILES,
        name="microsalt-name",
        ticket="123456",
    )
    application: Application = microsalt_configurator.store.get_application_by_tag("MWRNXTR003")
    customer: Customer = microsalt_configurator.store.get_customers()[0]
    organism: Organism = microsalt_configurator.store.get_all_organisms()[0]
    microsalt_sample: Sample = microsalt_configurator.store.add_sample(
        application_version=application.versions[0],
        customer=customer,
        name="microsalt-sample",
        organism=organism,
        priority=Priority.standard,
        sex=SexEnum.unknown,
    )
    microsalt_configurator.store.relate_sample(
        case=microsalt_case, sample=microsalt_sample, status=StatusEnum.unknown
    )
    microsalt_configurator.store.add_item_to_store(microsalt_case)
    microsalt_configurator.store.commit_to_store()

    with mock.patch.object(Path, "exists", return_value=True):
        # WHEN configuring the case
        config: MicrosaltCaseConfig = microsalt_configurator.configure(microsalt_case.internal_id)

        # THEN we should get a config back
        assert config


def test_configure_missing_organism(microsalt_configurator: MicrosaltConfigurator):
    # GIVEN a microSALT case containing a sample with a missing organism
    microsalt_case: Case = microsalt_configurator.store.add_case(
        customer_id=0,
        data_analysis=Workflow.MICROSALT,
        data_delivery=DataDelivery.ANALYSIS_FILES,
        name="microsalt-name",
        ticket="123456",
    )
    application: Application = microsalt_configurator.store.get_application_by_tag("MWRNXTR003")
    customer: Customer = microsalt_configurator.store.get_customers()[0]
    microsalt_sample: Sample = microsalt_configurator.store.add_sample(
        application_version=application.versions[0],
        customer=customer,
        name="microsalt-sample",
        priority=Priority.standard,
        sex=SexEnum.unknown,
    )
    microsalt_configurator.store.relate_sample(
        case=microsalt_case, sample=microsalt_sample, status=StatusEnum.unknown
    )
    microsalt_configurator.store.add_item_to_store(microsalt_case)
    microsalt_configurator.store.commit_to_store()

    with pytest.raises(CgDataError):
        # WHEN configuring the case
        microsalt_configurator.configure(microsalt_case.internal_id)
    # THEN the missing organism should raise a CgDataError


def test_get_config_path_success(microsalt_configurator: MicrosaltConfigurator):
    microsalt_case: Case = microsalt_configurator.store.add_case(
        customer_id=0,
        data_analysis=Workflow.MICROSALT,
        data_delivery=DataDelivery.ANALYSIS_FILES,
        name="microsalt-name",
        ticket="123456",
    )

    microsalt_configurator.store.add_item_to_store(microsalt_case)
    microsalt_configurator.store.commit_to_store()

    with mock.patch.object(Path, "exists", return_value=True):
        # WHEN configuring the case
        config = microsalt_configurator.get_config(microsalt_case.internal_id)

        assert config.case_id == microsalt_case.internal_id
        assert config.workflow == microsalt_case.data_analysis
        assert config.config_file_path == Path(
            microsalt_configurator.config_file_creator.queries_path,
            microsalt_case.internal_id + FileExtensions.JSON,
        )


def test_get_config_path_config_not_ready(microsalt_configurator: MicrosaltConfigurator):
    microsalt_case: Case = microsalt_configurator.store.add_case(
        customer_id=0,
        data_analysis=Workflow.MICROSALT,
        data_delivery=DataDelivery.ANALYSIS_FILES,
        name="microsalt-name",
        ticket="123456",
    )

    microsalt_configurator.store.add_item_to_store(microsalt_case)
    microsalt_configurator.store.commit_to_store()

    with pytest.raises(CaseNotConfiguredError):
        microsalt_configurator.get_config(microsalt_case.internal_id)
