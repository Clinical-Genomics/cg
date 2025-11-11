from unittest.mock import Mock, create_autospec

import pytest

from cg.apps.lims import LimsAPI
from cg.meta.workflow.fastq import MicrosaltFastqHandler
from cg.models.cg_config import (
    CGConfig,
    NalloConfig,
    RarediseaseConfig,
    RnafusionConfig,
    TaxprofilerConfig,
)
from cg.services.analysis_starter.configurator.file_creators.microsalt_config import (
    MicrosaltConfigFileCreator,
)
from cg.services.analysis_starter.configurator.file_creators.nextflow.config_file import (
    NextflowConfigFileCreator,
)
from cg.services.analysis_starter.configurator.file_creators.nextflow.params_file.nallo import (
    NalloParamsFileCreator,
)
from cg.services.analysis_starter.configurator.file_creators.nextflow.params_file.raredisease import (
    RarediseaseParamsFileCreator,
)
from cg.services.analysis_starter.configurator.file_creators.nextflow.params_file.rnafusion import (
    RNAFusionParamsFileCreator,
)
from cg.services.analysis_starter.configurator.file_creators.nextflow.params_file.taxprofiler import (
    TaxprofilerParamsFileCreator,
)
from cg.services.analysis_starter.configurator.file_creators.nextflow.sample_sheet.nallo import (
    NalloSampleSheetCreator,
)
from cg.services.analysis_starter.configurator.file_creators.nextflow.sample_sheet.raredisease import (
    RarediseaseSampleSheetCreator,
)
from cg.services.analysis_starter.configurator.file_creators.nextflow.sample_sheet.rnafusion import (
    RNAFusionSampleSheetCreator,
)
from cg.services.analysis_starter.configurator.file_creators.nextflow.sample_sheet.taxprofiler import (
    TaxprofilerSampleSheetCreator,
)
from cg.services.analysis_starter.configurator.implementations.microsalt import (
    MicrosaltConfigurator,
)
from cg.services.analysis_starter.configurator.implementations.nextflow import NextflowConfigurator
from cg.store.store import Store


@pytest.fixture
def microsalt_configurator(
    microsalt_config_file_creator: MicrosaltConfigFileCreator,
    cg_context: CGConfig,
    microsalt_fastq_handler: MicrosaltFastqHandler,
    lims_api: LimsAPI,
    microsalt_store: Store,
) -> MicrosaltConfigurator:
    return MicrosaltConfigurator(
        config_file_creator=microsalt_config_file_creator,
        fastq_handler=microsalt_fastq_handler,
        lims_api=lims_api,
        microsalt_config=cg_context.microsalt,
        store=microsalt_store,
    )


@pytest.fixture
def nallo_configurator(
    mock_store_for_nallo_file_creators: Store, nallo_config_object: NalloConfig
) -> NextflowConfigurator:
    return NextflowConfigurator(
        store=mock_store_for_nallo_file_creators,
        config_file_creator=create_autospec(NextflowConfigFileCreator),
        params_file_creator=create_autospec(NalloParamsFileCreator),
        pipeline_config=nallo_config_object,
        sample_sheet_creator=create_autospec(NalloSampleSheetCreator),
        pipeline_extension=Mock(),
    )


@pytest.fixture
def raredisease_configurator(
    mock_store_for_raredisease_file_creators: Store,
    raredisease_config_object: RarediseaseConfig,
) -> NextflowConfigurator:
    return NextflowConfigurator(
        store=mock_store_for_raredisease_file_creators,
        config_file_creator=create_autospec(NextflowConfigFileCreator),
        params_file_creator=create_autospec(RarediseaseParamsFileCreator),
        pipeline_config=raredisease_config_object,
        sample_sheet_creator=create_autospec(RarediseaseSampleSheetCreator),
        pipeline_extension=Mock(),
    )


@pytest.fixture
def rnafusion_configurator(
    mock_store_for_rnafusion_file_creators: Store,
    rnafusion_config_object: RnafusionConfig,
) -> NextflowConfigurator:
    return NextflowConfigurator(
        store=mock_store_for_rnafusion_file_creators,
        config_file_creator=create_autospec(NextflowConfigFileCreator),
        params_file_creator=create_autospec(RNAFusionParamsFileCreator),
        pipeline_config=rnafusion_config_object,
        sample_sheet_creator=create_autospec(RNAFusionSampleSheetCreator),
        pipeline_extension=Mock(),
    )


@pytest.fixture
def taxprofiler_configurator(
    mock_store_for_taxprofiler_file_creators: Store,
    taxprofiler_config_object: TaxprofilerConfig,
) -> NextflowConfigurator:
    return NextflowConfigurator(
        store=mock_store_for_taxprofiler_file_creators,
        config_file_creator=create_autospec(NextflowConfigFileCreator),
        params_file_creator=create_autospec(TaxprofilerParamsFileCreator),
        pipeline_config=taxprofiler_config_object,
        sample_sheet_creator=create_autospec(TaxprofilerSampleSheetCreator),
        pipeline_extension=Mock(),
    )
