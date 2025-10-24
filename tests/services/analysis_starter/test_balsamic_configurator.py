from pathlib import Path
from typing import cast
from unittest.mock import Mock, create_autospec

import pytest
from pytest_mock import MockerFixture

from cg.constants.priority import SlurmQos
from cg.exc import CaseNotConfiguredError
from cg.meta.workflow.fastq import BalsamicFastqHandler
from cg.models.cg_config import BalsamicConfig
from cg.services.analysis_starter.configurator.file_creators.balsamic_config import (
    BalsamicConfigFileCreator,
)
from cg.services.analysis_starter.configurator.implementations.balsamic import BalsamicConfigurator
from cg.services.analysis_starter.configurator.models.balsamic import BalsamicCaseConfig
from cg.store.models import Case, Sample
from cg.store.store import Store

PANEL_ONLY_FIELDS = ["soft_filter_normal", "panel_bed", "pon_cnn", "exome"]
WGS_ONLY_FIELDS = ["genome_interval", "gens_coverage_pon"]


@pytest.fixture
def case_with_sample() -> Case:
    case_with_sample: Case = create_autospec(Case)
    sample: Sample = create_autospec(Sample, internal_id="sample1")
    case_with_sample.samples = [sample]
    return case_with_sample


def test_get_config(balsamic_configurator: BalsamicConfigurator, case_id: str, tmp_path: Path):
    """Tests that the get_config method returns a BalsamicCaseConfig. And that fields can be overridden with flags."""
    # GIVEN a Balsamic configurator with an existing config file
    balsamic_configurator.root_dir = tmp_path
    Path(balsamic_configurator.root_dir, case_id).mkdir()
    Path(balsamic_configurator.root_dir, case_id, f"{case_id}.json").touch()

    # GIVEN that the database returns a case with the provided case_id
    case_to_configure: Case = create_autospec(
        Case, internal_id=case_id, slurm_priority=SlurmQos.NORMAL
    )
    balsamic_configurator.store.get_case_by_internal_id_strict = Mock(
        return_value=case_to_configure
    )

    # WHEN getting the config
    config: BalsamicCaseConfig = balsamic_configurator.get_config(
        case_id=case_id, qos=SlurmQos.EXPRESS
    )

    # THEN the config should be a BalsamicCaseConfig
    assert isinstance(config, BalsamicCaseConfig)

    # THEN the qos should be set to the provided value
    assert config.qos == SlurmQos.EXPRESS


def test_get_config_missing_config_file(
    balsamic_configurator: BalsamicConfigurator, case_id: str, tmp_path: Path
):
    """Tests that the get_config method raises an error if the config file is missing."""
    # GIVEN a BalsamicConfigurator
    balsamic_configurator.root_dir = tmp_path

    # GIVEN that the config file does not exist

    # GIVEN that the database returns a case with the provided case_id
    case_to_configure: Case = create_autospec(
        Case, internal_id=case_id, slurm_priority=SlurmQos.NORMAL
    )
    balsamic_configurator.store.get_case_by_internal_id_strict = Mock(
        return_value=case_to_configure
    )

    # WHEN getting the config
    # THEN it should raise a CaseNotConfiguredError
    with pytest.raises(CaseNotConfiguredError):
        balsamic_configurator.get_config(case_id=case_id)


def test_configure(cg_balsamic_config: BalsamicConfig, mocker: MockerFixture):
    # GIVEN a fastq handler
    fastq_handler: BalsamicFastqHandler = create_autospec(BalsamicFastqHandler)

    # GIVEN a BalsamicConfigFileCreator
    config_file_creator: BalsamicConfigFileCreator = create_autospec(BalsamicConfigFileCreator)

    # GIVEN a store
    store: Store = create_autospec(Store)
    store.get_case_by_internal_id_strict = Mock(
        return_value=create_autospec(Case, slurm_priority=SlurmQos.NORMAL)
    )

    # GIVEN Balsamic configurator
    balsamic_configurator = BalsamicConfigurator(
        config=cg_balsamic_config,
        config_file_creator=config_file_creator,
        fastq_handler=fastq_handler,
        store=store,
    )

    # GIVEN that all relevant paths exist
    mocker.patch.object(Path, "exists", return_value=True)

    # WHEN calling configure
    balsamic_case_config: BalsamicCaseConfig = balsamic_configurator.configure(case_id="case_id")

    # THEN the fastq files should be linked
    cast(Mock, fastq_handler.link_fastq_files).assert_called_once_with(case_id="case_id")

    # THEN the config file should be created
    cast(Mock, config_file_creator.create).assert_called_once_with(case_id="case_id")

    # THEN the case config is as expected
    assert balsamic_case_config == BalsamicCaseConfig(
        case_id="case_id",
        account=cg_balsamic_config.slurm.account,
        binary=cg_balsamic_config.binary_path,
        conda_binary=cg_balsamic_config.conda_binary,
        environment=cg_balsamic_config.conda_env,
        head_job_partition=cg_balsamic_config.head_job_partition,
        qos=SlurmQos.NORMAL,
        sample_config=Path(cg_balsamic_config.root, "case_id", "case_id.json"),
    )


def test_configure_with_flags(cg_balsamic_config: BalsamicConfig, mocker: MockerFixture):
    # GIVEN a fastq handler
    fastq_handler: BalsamicFastqHandler = create_autospec(BalsamicFastqHandler)

    # GIVEN a BalsamicConfigFileCreator
    config_file_creator: BalsamicConfigFileCreator = create_autospec(BalsamicConfigFileCreator)

    # GIVEN a store
    store: Store = create_autospec(Store)
    store.get_case_by_internal_id_strict = Mock(
        return_value=create_autospec(Case, slurm_priority=SlurmQos.NORMAL)
    )

    # GIVEN a Balsamic configurator
    balsamic_configurator = BalsamicConfigurator(
        config=cg_balsamic_config,
        config_file_creator=config_file_creator,
        fastq_handler=fastq_handler,
        store=store,
    )

    # GIVEN that all relevant paths exist
    mocker.patch.object(Path, "exists", return_value=True)

    # GIVEN that we have a workflow profile path
    workflow_profile = Path("workflow_profile")

    # WHEN calling configure
    balsamic_case_config: BalsamicCaseConfig = balsamic_configurator.configure(
        case_id="case_id", panel_bed="panel_bed", workflow_profile=workflow_profile
    )

    # THEN the fastq files should be linked
    cast(Mock, fastq_handler.link_fastq_files).assert_called_once_with(case_id="case_id")

    # THEN the config file should be created with the provided panel bed
    cast(Mock, config_file_creator.create).assert_called_once_with(
        case_id="case_id", panel_bed="panel_bed", workflow_profile=workflow_profile
    )

    # THEN the case config is as expected
    assert balsamic_case_config == BalsamicCaseConfig(
        case_id="case_id",
        account=cg_balsamic_config.slurm.account,
        binary=cg_balsamic_config.binary_path,
        conda_binary=cg_balsamic_config.conda_binary,
        environment=cg_balsamic_config.conda_env,
        head_job_partition=cg_balsamic_config.head_job_partition,
        qos=SlurmQos.NORMAL,
        sample_config=Path(cg_balsamic_config.root, "case_id", "case_id.json"),
        workflow_profile=workflow_profile,
    )
