from pathlib import Path
from unittest.mock import Mock, create_autospec

import pytest
from pytest_mock import MockerFixture

from cg.constants.priority import SlurmQos
from cg.services.analysis_starter.configurator.implementations import mip_dna
from cg.services.analysis_starter.configurator.implementations.mip_dna import MIPDNAConfigurator
from cg.services.analysis_starter.configurator.models.mip_dna import MIPDNACaseConfig
from cg.store.models import Case
from cg.store.store import Store


@pytest.fixture
def mock_status_db() -> Store:
    mock_store: Store = create_autospec(Store)
    mock_case: Case = create_autospec(Case, slurm_priority=SlurmQos.NORMAL)
    mock_store.get_case_by_internal_id_strict = Mock(return_value=mock_case)
    return mock_store


def test_configure(mocker: MockerFixture):
    # GIVEN a case id
    case_id = "test_case"

    store = create_autospec(Store)
    store.get_case_by_internal_id_strict = Mock(
        return_value=create_autospec(Case, slurm_priority=SlurmQos.NORMAL)
    )

    # GIVEN a MIP DNA configurator
    configurator = MIPDNAConfigurator(
        config_file_creator=Mock(),
        fastq_handler=Mock(),
        gene_panel_file_creator=Mock(),
        managed_variants_file_creator=Mock(),
        root=Path("root_dir"),
        store=store,
    )

    # GIVEN that we mock making the run directory
    mock_create_dir = mocker.patch.object(Path, "mkdir")

    # GIVEN a mocked version of _ensure_valid_config
    mock_validation = mocker.patch.object(configurator, "_ensure_valid_config")

    # WHEN configuring a case
    case_config: MIPDNACaseConfig = configurator.configure(
        case_id=case_id, panel_bed="bed_file.bed"
    )

    # THEN the run directory should have been created
    mock_create_dir.assert_called_with(parents=True, exist_ok=True)
    assert isinstance(case_config, MIPDNACaseConfig)

    # THEN the fastq handler should have been called with the case id
    configurator.fastq_handler.link_fastq_files.assert_called_once_with(case_id)

    # THEN the config file creator should have been called with the case id and the provided bed flag
    configurator.config_file_creator.create.assert_called_once_with(
        case_id=case_id, bed_flag="bed_file.bed"
    )

    # THEN the gene panel file creator should have been called with correct case id and path
    configurator.gene_panel_file_creator.create.assert_called_once_with(
        case_id=case_id, case_path=Path("root_dir", case_id)
    )

    configurator.managed_variants_file_creator.create.assert_called_once_with(
        case_id=case_id, case_path=Path("root_dir", case_id)
    )

    mock_validation.assert_called_once_with()


def test_get_config(mock_status_db: Store, mocker: MockerFixture):
    """Test that the MIP DNA configurator can get a case config."""

    # GIVEN an email address in the environment
    mocker.patch.object(mip_dna, "environ_email", return_value="test@scilifelab.se")

    # GIVEN a MIP DNA configurator
    configurator = MIPDNAConfigurator(
        config_file_creator=Mock(),
        fastq_handler=Mock(),
        gene_panel_file_creator=Mock(),
        managed_variants_file_creator=Mock(),
        root=Path("root_dir"),
        store=mock_status_db,
    )

    # GIVEN a case ID
    case_id = "test_case"

    # WHEN getting the case config
    case_config: MIPDNACaseConfig = configurator.get_config(case_id=case_id)

    # THEN case_id, slurm_qos and email should be set
    assert case_config.case_id == "test_case"
    assert case_config.slurm_qos == SlurmQos.NORMAL
    assert case_config.email == "test@scilifelab.se"
    assert case_config.start_after_recipe is None
    assert case_config.start_with_recipe is None


def test_get_config_all_flags_set(mock_status_db: Store):
    """Test that the MIP DNA configurator can get a case config."""

    # GIVEN a MIP DNA configurator
    configurator = MIPDNAConfigurator(
        config_file_creator=Mock(),
        fastq_handler=Mock(),
        gene_panel_file_creator=Mock(),
        managed_variants_file_creator=Mock(),
        root=Path("root_dir"),
        store=mock_status_db,
    )

    # GIVEN a case ID
    case_id = "test_case"

    # WHEN getting the case config
    case_config: MIPDNACaseConfig = configurator.get_config(
        case_id=case_id,
        start_after_recipe="banana_bread",
        start_with_recipe="short_bread",
        use_bwa_mem=True,
    )

    # THEN we should run the analysis with bwa_mem instead of bwa_mem2
    assert case_config.bwa_mem == 1
    assert case_config.bwa_mem2 == 0
    assert getattr(case_config, "use_bwa_mem", None) is None

    assert case_config.start_after_recipe == "banana_bread"
    assert case_config.start_with_recipe == "short_bread"
