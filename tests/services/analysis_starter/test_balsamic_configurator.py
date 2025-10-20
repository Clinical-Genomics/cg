from pathlib import Path
from typing import cast
from unittest.mock import Mock, create_autospec

import pytest
from pytest_mock import MockerFixture

from cg.constants.priority import SlurmQos
from cg.exc import BedFileNotFoundError, CaseNotConfiguredError
from cg.meta.workflow.fastq import BalsamicFastqHandler
from cg.models.cg_config import BalsamicConfig
from cg.services.analysis_starter.configurator.file_creators.balsamic_config import (
    BalsamicConfigFileCreator,
)
from cg.services.analysis_starter.configurator.implementations.balsamic import BalsamicConfigurator
from cg.services.analysis_starter.configurator.models.balsamic import BalsamicCaseConfig
from cg.store.models import BedVersion, Case, Sample
from cg.store.store import Store

PANEL_ONLY_FIELDS = ["soft_filter_normal", "panel_bed", "pon_cnn", "exome"]
WGS_ONLY_FIELDS = ["genome_interval", "gens_coverage_pon"]


@pytest.fixture
def case_with_sample() -> Case:
    case_with_sample: Mock[Case] = create_autospec(Case)
    sample: Mock[Sample] = create_autospec(Sample, internal_id="sample1")
    case_with_sample.samples = [sample]
    return case_with_sample


def test_resolve_bed_file_correct_in_lims(
    balsamic_configurator: BalsamicConfigurator, case_with_sample: Case
):
    """Test that the correct bed file is resolved when it exists in LIMS."""
    # GIVEN a Balsamic configurator with a bed_directory
    bed_directory = Path("path/to/bed/files")
    balsamic_configurator.bed_directory = bed_directory

    # GIVEN a case with a sample

    # GIVEN that the sample has a panel set in LIMS
    balsamic_configurator.lims_api.capture_kit = Mock(return_value="GMS_duck")

    # GIVEN that the panel exists in the store
    balsamic_configurator.store.get_bed_version_by_short_name = Mock(
        return_value=create_autospec(BedVersion, filename="GMS_duck_v5.99_extra_floating.bed")
    )

    # WHEN resolving the bed file
    bed_file = balsamic_configurator._resolve_bed_file(case_with_sample)

    # THEN the correct bed file should be returned
    assert bed_file == Path(bed_directory, "GMS_duck_v5.99_extra_floating.bed")


def test_resolve_bed_file_not_in_store(
    balsamic_configurator: BalsamicConfigurator, case_with_sample: Case
):
    """Test that an error is raised when the panel does not exist in the store."""
    # GIVEN a Balsamic configurator with a bed_directory
    bed_directory = Path("path/to/bed/files")
    balsamic_configurator.bed_directory = bed_directory

    # GIVEN a case with a sample

    # GIVEN that the sample has a panel set in LIMS
    balsamic_configurator.lims_api.capture_kit = Mock(return_value="GMS_duck")

    # GIVEN that the panel does not exist in the store
    balsamic_configurator.store.get_bed_version_by_short_name = Mock(return_value=None)

    # WHEN resolving the bed file
    # THEN it should raise a ValueError
    with pytest.raises(BedFileNotFoundError):
        balsamic_configurator._resolve_bed_file(case_with_sample)


def test_resolve_bed_file_override_with_flag(
    balsamic_configurator: BalsamicConfigurator, case_with_sample: Case
):
    """Test that the bed file can be overridden with a flag."""
    # GIVEN a Balsamic configurator with a bed_directory
    bed_directory = Path("path/to/bed/files")
    balsamic_configurator.bed_directory = bed_directory

    # GIVEN a case with a sample

    # GIVEN that the sample has a panel set in LIMS
    balsamic_configurator.lims_api.capture_kit = Mock(return_value=None)

    # GIVEN that the panel exists in the store
    balsamic_configurator.store.get_bed_version_by_short_name = Mock(
        return_value=create_autospec(BedVersion, filename="NACG_goose_1_99_max_fluff.bed")
    )

    # WHEN resolving the bed file with an override flag
    provided_bed_name = Path("NACG_goose")
    bed_file = balsamic_configurator._resolve_bed_file(
        case_with_sample, panel_bed=provided_bed_name
    )

    # THEN the overridden bed file should be returned
    assert bed_file == Path(bed_directory, "NACG_goose_1_99_max_fluff.bed")

    # THEN the LIMS API should not be called
    balsamic_configurator.lims_api.capture_kit.assert_not_called()


def test_get_bed_name_from_lims_missing_panel(
    balsamic_configurator: BalsamicConfigurator, case_with_sample: Case
):
    """Test that an error is raised when the panel is not set in LIMS."""
    # GIVEN a Balsamic configurator with a bed_directory
    bed_directory = Path("path/to/bed/files")
    balsamic_configurator.bed_directory = bed_directory

    # GIVEN a case with a sample

    # GIVEN that the sample does not have a panel set in LIMS
    balsamic_configurator.lims_api.capture_kit = Mock(return_value=None)

    # WHEN resolving the bed file
    # THEN it should raise a ValueError
    with pytest.raises(BedFileNotFoundError):
        balsamic_configurator._resolve_bed_file(case_with_sample)


def test_get_config(balsamic_configurator: BalsamicConfigurator, case_id: str, tmp_path: Path):
    """Tests that the get_config method returns a BalsamicCaseConfig. And that fields can be overridden with flags."""
    # GIVEN a Balsamic configurator with an existing config file
    balsamic_configurator.root_dir = tmp_path
    Path(balsamic_configurator.root_dir, case_id).mkdir()
    Path(balsamic_configurator.root_dir, case_id, f"{case_id}.json").touch()

    # GIVEN that the database returns a case with the provided case_id
    case_to_configure: Mock[Case] = create_autospec(Case, internal_id=case_id)
    case_to_configure.slurm_priority = SlurmQos.NORMAL
    balsamic_configurator.store.get_case_by_internal_id = Mock(return_value=case_to_configure)

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
    case_to_configure: Mock[Case] = create_autospec(Case, internal_id=case_id)
    case_to_configure.slurm_priority = SlurmQos.NORMAL
    balsamic_configurator.store.get_case_by_internal_id = Mock(return_value=case_to_configure)

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
        lims_api=Mock(),
        store=store,
    )

    # GIVEN that all relevant paths exist
    mocker.patch.object(Path, "exists", return_value=True)

    # WHEN calling configure
    balsamic_configurator.configure(case_id="case_id")

    # THEN the fastq files should be linked
    cast(Mock, fastq_handler.link_fastq_files).assert_called_once_with(case_id="case_id")

    # THEN the config file should be created
    cast(Mock, config_file_creator.create).assert_called_once_with(case_id="case_id")


# TODO add flag test
