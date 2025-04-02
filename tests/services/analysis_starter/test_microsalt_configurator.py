from pathlib import Path
from unittest import mock

from cg.constants import DataDelivery, FileExtensions, Workflow
from cg.io.controller import WriteFile
from cg.services.analysis_starter.configurator.implementations.microsalt import (
    MicrosaltConfigurator,
)
from cg.services.analysis_starter.configurator.models.microsalt import MicrosaltCaseConfig
from cg.store.models import Case


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
    microsalt_configurator.store.add_item_to_store(microsalt_case)
    microsalt_configurator.store.commit_to_store()

    # WHEN configuring a case
    with mock.patch.object(WriteFile, "write_file_from_content", return_value=None):
        config: MicrosaltCaseConfig = microsalt_configurator.configure(microsalt_case.internal_id)

    # THEN we should get a config back
    assert config.case_id == microsalt_case.internal_id
    assert config.workflow == microsalt_case.data_analysis
    assert config.config_file_path == Path(
        microsalt_configurator.config_file_creator.queries_path,
        microsalt_case.internal_id + FileExtensions.JSON,
    )
