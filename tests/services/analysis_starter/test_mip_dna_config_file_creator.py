from pathlib import Path
from unittest.mock import Mock, create_autospec

import pytest
from pytest_mock import MockerFixture

from cg.services.analysis_starter.configurator.file_creators import mip_dna_config
from cg.services.analysis_starter.configurator.file_creators.mip_dna_config import (
    MIPDNAConfigFileCreator,
)
from cg.store.models import Case, CaseSample, Sample
from cg.store.store import Store


@pytest.fixture
def expected_content() -> dict:
    """Fixture to provide expected content for the MIP DNA config file."""
    return {
        "case": "case_id",
        "default_gene_panels": [],
        "samples": [
            {
                "analysis_type": "",
                "capture_kit": "mock_bed_file",
                "expected_coverage": "",
                "father": "",
                "mother": "",
                "phenotype": "",
                "sample_display_name": "",
                "sample_id": "",
                "sex": "",
            },
        ],
    }


def test_create(expected_content: dict, mocker: MockerFixture):
    # GIVEN a mocked store
    sample = create_autospec(Sample)
    case_sample: CaseSample = create_autospec(CaseSample, sample=sample)
    case_id = "case_id"
    case: Case = create_autospec(Case, internal_id=case_id, links=[case_sample])
    store: Store = create_autospec(Store)
    store.get_case_by_internal_id_strict = Mock(return_value=case)

    # GIVEN a MIPDNAConfigFileCreator
    file_creator = MIPDNAConfigFileCreator(lims_api=Mock(), store=store)

    # GIVEN a patched writer
    mock_write = mocker.patch.object(mip_dna_config, "write_yaml")

    # WHEN creating the config file
    file_creator.create(case_id=case_id, bed_flag=None)

    # THEN the writer is called with the correct content and file path
    mock_write.assert_called_once_with(content=expected_content, file_path=Path("."))
