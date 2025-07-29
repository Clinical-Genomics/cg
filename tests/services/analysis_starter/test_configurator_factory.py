import pytest

from cg.constants import Workflow
from cg.models.cg_config import CGConfig
from cg.services.analysis_starter.configurator.configurator import Configurator
from cg.services.analysis_starter.configurator.implementations.balsamic import BalsamicConfigurator
from cg.services.analysis_starter.configurator.implementations.microsalt import (
    MicrosaltConfigurator,
)
from cg.services.analysis_starter.configurator.implementations.nextflow import NextflowConfigurator
from cg.services.analysis_starter.factories.configurator_factory import ConfiguratorFactory


@pytest.mark.parametrize(
    "workflow, configurator_type",
    [
        (Workflow.BALSAMIC, BalsamicConfigurator),
        (Workflow.MICROSALT, MicrosaltConfigurator),
        (Workflow.RAREDISEASE, NextflowConfigurator),
        (Workflow.RNAFUSION, NextflowConfigurator),
    ],
)
def test_configurator_factory_success(
    cg_context: CGConfig, workflow: Workflow, configurator_type: type[Configurator]
):
    # GIVEN a workflow we have support for

    # GIVEN a configurator factory
    configurator_factory = ConfiguratorFactory(cg_config=cg_context)

    # WHEN getting the configurator for the workflow
    configurator: Configurator = configurator_factory.get_configurator(workflow)

    # THEN the configurator is of the expected type
    assert isinstance(configurator, configurator_type)


def test_configurator_factory_failure(cg_context: CGConfig):
    # GIVEN a workflow we do not have support for
    workflow = Workflow.MIP_DNA

    # GIVEN a configurator factory
    configurator_factory = ConfiguratorFactory(cg_config=cg_context)

    # WHEN getting the configurator for the workflow

    # THEN a NotImplementedError should be raised
    with pytest.raises(NotImplementedError):
        configurator_factory.get_configurator(workflow)
