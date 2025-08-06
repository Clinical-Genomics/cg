from pathlib import Path
from unittest.mock import Mock, create_autospec

from pytest_mock import MockerFixture

from cg.services.analysis_starter.configurator.file_creators import mip_dna_config
from cg.services.analysis_starter.configurator.file_creators.mip_dna_config import (
    MIPDNAConfigFileCreator,
)
from cg.store.models import Case, Sample
from cg.store.store import Store


def test_create(mocker: MockerFixture):
    # GIVEN a mocked store
    sample = create_autospec(Sample)
    case = create_autospec(Case, samples=[sample])
    store = create_autospec(Store, get_case_by_internal_id_strict=case)

    # GIVEN a MIPDNAConfigFileCreator
    file_creator = MIPDNAConfigFileCreator(lims_api=Mock(), store=store)

    # GIVEN a patched writer
    mock_write = mocker.patch.object(mip_dna_config, "write_yaml")

    # WHEN creating the config file
    file_creator.create(case_id="case_id", bed_flag=None)

    # THEN the writer is called with the correct content and file path
    mock_write.assert_called_once_with(content="expected_content", file_path=Path("expected_path"))
