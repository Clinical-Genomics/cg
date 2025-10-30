from typing import cast
from unittest.mock import create_autospec

import pytest

from cg.constants import Workflow
from cg.meta.workflow.fastq import MicrosaltFastqHandler, MipFastqHandler
from cg.models.cg_config import CGConfig, MipConfig
from cg.services.analysis_starter.configurator.configurator import Configurator
from cg.services.analysis_starter.configurator.extensions.abstract import PipelineExtension
from cg.services.analysis_starter.configurator.extensions.nallo import NalloExtension
from cg.services.analysis_starter.configurator.extensions.raredisease import RarediseaseExtension
from cg.services.analysis_starter.configurator.file_creators.gene_panel import GenePanelFileCreator
from cg.services.analysis_starter.configurator.file_creators.managed_variants import (
    ManagedVariantsFileCreator,
)
from cg.services.analysis_starter.configurator.file_creators.microsalt_config import (
    MicrosaltConfigFileCreator,
)
from cg.services.analysis_starter.configurator.file_creators.mip_dna_config import (
    MIPDNAConfigFileCreator,
)
from cg.services.analysis_starter.configurator.file_creators.nextflow.params_file.abstract import (
    ParamsFileCreator,
)
from cg.services.analysis_starter.configurator.file_creators.nextflow.sample_sheet.protocol import (
    SampleSheetCreator,
)
from cg.services.analysis_starter.configurator.implementations.microsalt import (
    MicrosaltConfigurator,
)
from cg.services.analysis_starter.configurator.implementations.mip_dna import MIPDNAConfigurator
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
    "workflow, pipeline_extension_class",
    [
        (Workflow.NALLO, NalloExtension),
        (Workflow.RAREDISEASE, RarediseaseExtension),
        (Workflow.RNAFUSION, PipelineExtension),
        (Workflow.TAXPROFILER, PipelineExtension),
    ],
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
    assert isinstance(configurator.sample_sheet_creator, SampleSheetCreator)
    assert isinstance(configurator.pipeline_extension, PipelineExtension)


def test_get_mip_dna_configurator():
    # GIVEN a MIP-DNA config
    mip_config: MipConfig = create_autospec(
        MipConfig,
        root="mip_root",
        conda_binary="conda_binary",
        conda_env="S_mip_dna",
        mip_config="mip_config",
        workflow="analyse rd_dna",
        script="script",
    )
    cg_config: CGConfig = create_autospec(CGConfig, mip_rd_dna=mip_config)

    # GIVEN a configurator factory
    configurator_factory = ConfiguratorFactory(cg_config=cg_config)

    # WHEN getting the configurator for the MIP-DNA workflow
    configurator: Configurator = configurator_factory.get_configurator(Workflow.MIP_DNA)

    # THEN the configurator is of type MIPDNAConfigurator
    assert isinstance(configurator, MIPDNAConfigurator)

    # THEN the config file creator is of type MIPDNAConfigFileCreator
    assert isinstance(configurator.config_file_creator, MIPDNAConfigFileCreator)

    # THEN the fastq handler is of type MipFastqHandler
    assert isinstance(configurator.fastq_handler, MipFastqHandler)

    # THEN the gene panel file creator should be an instance of GenePanelFileCreator
    assert isinstance(configurator.gene_panel_file_creator, GenePanelFileCreator)

    # THEN the managed variants file creator should be an instance of ManagedVariantsFileCreator
    assert isinstance(configurator.managed_variants_file_creator, ManagedVariantsFileCreator)


def test_configurator_factory_failure(cg_context: CGConfig):
    # GIVEN a workflow we do not have support for
    workflow = Workflow.BALSAMIC

    # GIVEN a configurator factory
    configurator_factory = ConfiguratorFactory(cg_config=cg_context)

    # WHEN getting the configurator for the workflow

    # THEN a NotImplementedError should be raised
    with pytest.raises(NotImplementedError):
        configurator_factory.get_configurator(workflow)
