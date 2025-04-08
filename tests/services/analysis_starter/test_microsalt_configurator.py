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


@pytest.fixture
def microsalt_case(microsalt_configurator: MicrosaltConfigurator) -> Case:
    return microsalt_configurator.store.get_cases()[0]


@pytest.fixture
def microsalt_sample(microsalt_case: Case) -> Sample:
    return microsalt_case.samples[0]


def test_configure_success(microsalt_configurator: MicrosaltConfigurator, microsalt_case: Case):
    # GIVEN a microSALT configurator

    # GIVEN a microSALT case
    organism: Organism = microsalt_configurator.store.get_all_organisms()[0]
    microsalt_sample.organism = organism

    with mock.patch.object(Path, "exists", return_value=True):
        # WHEN configuring the case
        config: MicrosaltCaseConfig = microsalt_configurator.configure(microsalt_case.internal_id)

        # THEN we should get a config back
        assert config


def test_configure_missing_organism(
    microsalt_configurator: MicrosaltConfigurator, microsalt_case: Case, microsalt_sample: Sample
):
    # GIVEN a microSALT case containing a sample with a missing organism
    microsalt_sample.organism = None

    with pytest.raises(CgDataError):
        # WHEN configuring the case
        microsalt_configurator.configure(microsalt_case.internal_id)
        # THEN the missing organism should raise a CgDataError


def test_get_config_path_success(
    microsalt_configurator: MicrosaltConfigurator, microsalt_case: Case, microsalt_sample: Sample
):
    # GIVEN a microSALT case
    # GIVEN that the config file exists
    with mock.patch.object(Path, "exists", return_value=True):
        # WHEN getting the config object
        config = microsalt_configurator.get_config(microsalt_case.internal_id)

        # THEN the returned configuration should be correct
        assert config.case_id == microsalt_case.internal_id
        assert config.workflow == Workflow.MICROSALT
        assert config.config_file_path == Path(
            microsalt_configurator.config_file_creator.queries_path,
            microsalt_case.internal_id + FileExtensions.JSON,
        )


def test_get_config_path_config_not_ready(
    microsalt_configurator: MicrosaltConfigurator, microsalt_case: Case
):
    # GIVEN a microSALT case with no existing config file

    with pytest.raises(CaseNotConfiguredError):
        # WHEN getting the config object
        microsalt_configurator.get_config(microsalt_case.internal_id)
        # THEN it raises a CaseNotConfiguredError
