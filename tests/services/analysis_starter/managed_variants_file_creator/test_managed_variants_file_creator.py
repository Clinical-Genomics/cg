from pytest_mock import MockerFixture

from cg.apps.scout.scoutapi import ScoutAPI
from cg.services.analysis_starter.configurator.file_creators import managed_variants
from cg.services.analysis_starter.configurator.file_creators.managed_variants import (
    ManagedVariantsFileCreator,
)


def test_managed_variants_content(
    raredisease_managed_variants_creator: ManagedVariantsFileCreator,
    raredisease_case_id: str,
    raredisease_managed_variants_file_content: list[str],
    mocker: MockerFixture,
):
    """Test that the managed variants file content is created correctly."""
    # GIVEN a Raredisease managed variants file content creator and a case path

    # GIVEN a mock of Scout variants
    mocker.patch.object(managed_variants, "write_txt")

    # WHEN creating a managed variants file
    expected_content_fixture: list[str] = raredisease_managed_variants_file_content
    mocker.patch.object(ScoutAPI, "export_managed_variants", return_value=expected_content_fixture)

    raredisease_managed_variants_creator.create(raredisease_case_id)

    # THEN the content of the file is the expected
    assert content == expected_content_fixture
