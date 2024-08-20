"""Module to test fetching of file tags for file_delivery."""

from cg.constants import Workflow
from cg.constants.delivery import PIPELINE_ANALYSIS_TAG_MAP
from cg.services.file_delivery.fetch_delivery_files_tags.fetch_sample_and_case_delivery_file_tags_service import (
    FetchSampleAndCaseDeliveryFileTagsService,
)
from cg.services.file_delivery.fetch_delivery_files_tags.models import DeliveryFileTags


def test_fetch_tags():
    """Test to fetch tags for the files to deliver."""
    # GIVEN a workflow

    # WHEN fetching the tags for the files to deliver
    tags: DeliveryFileTags = FetchSampleAndCaseDeliveryFileTagsService().fetch_tags(
        Workflow.BALSAMIC
    )

    # THEN assert that the tags are fetched
    assert tags.case_tags == PIPELINE_ANALYSIS_TAG_MAP[Workflow.BALSAMIC]["case_tags"]
    assert tags.sample_tags == PIPELINE_ANALYSIS_TAG_MAP[Workflow.BALSAMIC]["sample_tags"]
