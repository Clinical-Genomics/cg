from typing import cast

import pytest

from cg.constants import Workflow
from cg.meta.workflow.fastq import MicrosaltFastqHandler
from cg.models.cg_config import CGConfig
from cg.services.analysis_starter.configurator.configurator import Configurator
from cg.services.analysis_starter.configurator.extensions.abstract import PipelineExtension
from cg.services.analysis_starter.configurator.file_creators.microsalt_config import (
    MicrosaltConfigFileCreator,
)
from cg.services.analysis_starter.configurator.file_creators.nextflow.params_file.abstract import (
    ParamsFileCreator,
)
from cg.services.analysis_starter.configurator.file_creators.nextflow.sample_sheet.creator import (
    NextflowSampleSheetCreator,
)
from cg.services.analysis_starter.configurator.implementations.microsalt import (
    MicrosaltConfigurator,
)
from cg.services.analysis_starter.configurator.implementations.nextflow import NextflowConfigurator
from cg.services.analysis_starter.factories.configurator_factory import ConfiguratorFactory


def test_get_microsalt_configurator(cg_context: CGConfig):
    # GIVEN a configurator factory
    configurator_factory = ConfiguratorFactory(cg_config=cg_context)

    # WHEN getting the configurator for the microSALT workflow
    configurator: Configurator = configurator_factory.get_configurator(Workflow.MICROSALT)

    # THEN the configurator is of type MicrosaltConfigurator
    assert isinstance(configurator, MicrosaltConfigurator)

    # THEN the config file creator is of type MicrosaltConfigFileCreator
    assert isinstance(configurator.config_file_creator, MicrosaltConfigFileCreator)

    # THEN the fastq handler is of type MicrosaltFastqHandler
    assert isinstance(configurator.fastq_handler, MicrosaltFastqHandler)


@pytest.mark.parametrize(
    "workflow",
    [Workflow.RAREDISEASE, Workflow.RNAFUSION, Workflow.TAXPROFILER],
)
def test_nextflow_configurator_factory_success(
    cg_context: CGConfig,
    workflow: Workflow,
):
    # GIVEN a workflow we have support for

    # GIVEN a configurator factory
    configurator_factory = ConfiguratorFactory(cg_config=cg_context)

    # WHEN getting the configurator for the workflow
    configurator = cast(NextflowConfigurator, configurator_factory.get_configurator(workflow))

    # THEN the configurator is of the expected type
    assert isinstance(configurator, NextflowConfigurator)
    assert isinstance(configurator.params_file_creator, ParamsFileCreator)
    assert isinstance(configurator.sample_sheet_creator, NextflowSampleSheetCreator)
    assert isinstance(configurator.pipeline_extension, PipelineExtension)


def test_configurator_factory_failure(cg_context: CGConfig):
    # GIVEN a workflow we do not have support for
    workflow = Workflow.BALSAMIC

    # GIVEN a configurator factory
    configurator_factory = ConfiguratorFactory(cg_config=cg_context)

    # WHEN getting the configurator for the workflow

    # THEN a NotImplementedError should be raised
    with pytest.raises(NotImplementedError):
        configurator_factory.get_configurator(workflow)
