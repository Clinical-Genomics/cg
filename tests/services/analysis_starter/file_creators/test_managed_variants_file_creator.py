from pathlib import Path
from unittest.mock import Mock, create_autospec

import pytest
from pytest_mock import MockerFixture

from cg.apps.scout.scoutapi import ScoutAPI
from cg.constants import Workflow
from cg.services.analysis_starter.configurator.file_creators import managed_variants
from cg.services.analysis_starter.configurator.file_creators.managed_variants import (
    ManagedVariantsFileCreator,
)
from cg.store.models import Case
from cg.store.store import Store


@pytest.fixture
def managed_variants_file_content() -> list[str]:
    return ["variant_from_scout1", "variant_from_scout2"]


@pytest.fixture
def managed_variants_creator(
    managed_variants_file_content: list[str],
) -> ManagedVariantsFileCreator:

    store: Store = create_autospec(Store)
    case = create_autospec(Case, data_analysis=Workflow.RAREDISEASE)
    store.get_case_by_internal_id = Mock(return_value=case)

    scout_api: ScoutAPI = create_autospec(ScoutAPI)
    scout_api.export_managed_variants = Mock(return_value=managed_variants_file_content)

    return ManagedVariantsFileCreator(
        store=store,
        scout_api=scout_api,
    )


def test_managed_variants_content(
    managed_variants_creator: ManagedVariantsFileCreator,
    managed_variants_file_content: list[str],
    mocker: MockerFixture,
):
    """Test that the managed variants file content is created correctly."""

    # GIVEN a mocked write_txt
    mocked_write_txt = mocker.patch.object(managed_variants, "write_txt_with_newlines")

    # WHEN creating a managed variants file
    managed_variants_creator.create(case_id="case_id", file_path=Path("managed_variants.vcf"))

    # THEN the content of the file is the expected
    mocked_write_txt.assert_called_once_with(
        file_path=Path("managed_variants.vcf"), content=managed_variants_file_content
    )
