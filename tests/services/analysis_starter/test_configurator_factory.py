from typing import cast
from unittest.mock import create_autospec

import pytest

from cg.apps.scout.scoutapi import ScoutAPI
from cg.constants import Workflow
from cg.meta.workflow.fastq import BalsamicFastqHandler, MicrosaltFastqHandler, MipFastqHandler
from cg.models.cg_config import BalsamicConfig, CGConfig, MipConfig
from cg.services.analysis_starter.configurator.configurator import Configurator
from cg.services.analysis_starter.configurator.extensions.nallo import NalloExtension
from cg.services.analysis_starter.configurator.extensions.pipeline_extension import (
    PipelineExtension,
)
from cg.services.analysis_starter.configurator.extensions.raredisease import RarediseaseExtension
from cg.services.analysis_starter.configurator.extensions.tomte_extension import TomteExtension
from cg.services.analysis_starter.configurator.file_creators.balsamic_config import (
    BalsamicConfigFileCreator,
)
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
from cg.services.analysis_starter.configurator.implementations.balsamic import BalsamicConfigurator
from cg.services.analysis_starter.configurator.implementations.microsalt import (
    MicrosaltConfigurator,
)
from cg.services.analysis_starter.configurator.implementations.mip_dna import MIPDNAConfigurator
from cg.services.analysis_starter.configurator.implementations.nextflow import NextflowConfigurator
from cg.services.analysis_starter.factories.configurator_factory import ConfiguratorFactory


def test_get_balsamic_configurator(cg_balsamic_config: BalsamicConfig):
    # GIVEN a CG Balsamic config
    cg_config: CGConfig = create_autospec(CGConfig, balsamic=cg_balsamic_config)

    # GIVEN a configurator factory
    configurator_factory = ConfiguratorFactory(cg_config=cg_config)

    # WHEN getting the configurator for the Balsamic workflow
    configurator: Configurator = configurator_factory.get_configurator(Workflow.BALSAMIC)

    # THEN the configurator is of type BalsamicConfigurator
    assert isinstance(configurator, BalsamicConfigurator)

    # THEN the config file creator is of type BalsamicConfigFileCreator
    assert isinstance(configurator.config_file_creator, BalsamicConfigFileCreator)

    # THEN the fastq handler is of type BalsamicFastqHandler
    assert isinstance(configurator.fastq_handler, BalsamicFastqHandler)


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
        (Workflow.RNAFUSION, PipelineExtension),
        (Workflow.TAXPROFILER, PipelineExtension),
        (Workflow.TOMTE, TomteExtension),
    ],
)
def test_nextflow_configurator_factory_success(
    cg_context: CGConfig,
    workflow: Workflow,
    pipeline_extension_class: type,
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
    assert isinstance(configurator.pipeline_extension, pipeline_extension_class)


def test_nextflow_configurator_factory_raredisease_success(
    cg_context: CGConfig,
):
    # GIVEN a configurator factory
    configurator_factory = ConfiguratorFactory(cg_config=cg_context)

    # WHEN getting the configurator for the workflow
    configurator = cast(
        NextflowConfigurator, configurator_factory.get_configurator(Workflow.RAREDISEASE)
    )

    # THEN the configurator is of the expected type
    assert isinstance(configurator, NextflowConfigurator)
    assert isinstance(configurator.params_file_creator, ParamsFileCreator)
    assert isinstance(configurator.sample_sheet_creator, SampleSheetCreator)
    assert isinstance(configurator.pipeline_extension, RarediseaseExtension)
    assert (
        configurator.pipeline_extension.gene_panel_file_creator.scout_api == cg_context.scout_api_38
    )
    assert (
        configurator.pipeline_extension.managed_variants_file_creator.scout_api
        == cg_context.scout_api_38
    )


def test_nextflow_configurator_factory_nallo_success(
    cg_context: CGConfig,
):
    # GIVEN a configurator factory
    configurator_factory = ConfiguratorFactory(cg_config=cg_context)

    # WHEN getting the configurator for the workflow
    configurator = cast(NextflowConfigurator, configurator_factory.get_configurator(Workflow.NALLO))

    # THEN the configurator is of the expected type
    assert isinstance(configurator, NextflowConfigurator)
    assert isinstance(configurator.params_file_creator, ParamsFileCreator)
    assert isinstance(configurator.sample_sheet_creator, SampleSheetCreator)
    assert isinstance(configurator.pipeline_extension, NalloExtension)
    assert (
        configurator.pipeline_extension.gene_panel_file_creator.scout_api == cg_context.scout_api_38
    )


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
    workflow = Workflow.FLUFFY

    # GIVEN a configurator factory
    configurator_factory = ConfiguratorFactory(cg_config=cg_context)

    # WHEN getting the configurator for the workflow

    # THEN a NotImplementedError should be raised
    with pytest.raises(NotImplementedError):
        configurator_factory.get_configurator(workflow)


@pytest.mark.parametrize(
    "workflow, scout_instance",
    [
        (Workflow.BALSAMIC, "scout_api_37"),
        (Workflow.BALSAMIC_UMI, "scout_api_37"),
        (Workflow.MIP_DNA, "scout_api_37"),
        (Workflow.MIP_RNA, "scout_api_37"),
        (Workflow.NALLO, "scout_api_38"),
        (Workflow.RAREDISEASE, "scout_api_38"),
        (Workflow.TOMTE, "scout_api_37"),
    ],
)
def test_get_scout_api(workflow: Workflow, scout_instance: str, cg_context: CGConfig):
    # GIVEN a configurator factory
    configurator_factory = ConfiguratorFactory(cg_config=cg_context)

    # WHEN getting the scout api instance for a given workflow
    scout_api: ScoutAPI = configurator_factory._get_scout_api(workflow=workflow)

    # THEN we should receive the correct scout instance
    assert scout_api == getattr(cg_context, scout_instance)
