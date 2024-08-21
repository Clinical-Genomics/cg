"""Module to test fetching of file tags for delivery."""

from cg.constants import Workflow
from cg.constants.delivery import PIPELINE_ANALYSIS_TAG_MAP
from cg.services.delivery.fetch_delivery_files_tags.exc import FetchDeliveryFileTagsError
from cg.services.delivery.fetch_delivery_files_tags.fetch_sample_and_case_delivery_file_tags_service import (
    FetchSampleAndCaseDeliveryFileTagsService,
)
from cg.services.delivery.fetch_delivery_files_tags.models import DeliveryFileTags
import pytest


@pytest.mark.parametrize(
    "workflow",
    [
        Workflow.BALSAMIC,
        Workflow.FASTQ,
        Workflow.MIP_DNA,
        Workflow.MIP_RNA,
        Workflow.BALSAMIC_QC,
        Workflow.MICROSALT,
        Workflow.TOMTE,
    ],
)
def test_fetch_tags(workflow: Workflow):
    """Test to fetch tags for the files to deliver."""
    # GIVEN a workflow and a tag fetcher
    tag_fetcher = FetchSampleAndCaseDeliveryFileTagsService()

    # WHEN fetching the tags for the files to deliver
    tags: DeliveryFileTags = tag_fetcher.fetch_tags(workflow)

    # THEN assert that the tags are fetched
    assert tags.case_tags == PIPELINE_ANALYSIS_TAG_MAP[workflow]["case_tags"]
    assert tags.sample_tags == PIPELINE_ANALYSIS_TAG_MAP[workflow]["sample_tags"]


def test_fetch_tags_unsupported_workflow():
    """Test to fetch tags for the files to deliver."""
    # GIVEN an unsupported workflow and a tag fetcher
    unsupported_workflow: str = "workflow_not_supported"
    tag_fetcher = FetchSampleAndCaseDeliveryFileTagsService()

    # WHEN fetching the tags for the files to deliver

    # THEN a FetchDeliveryFileTagsError should be raised
    with pytest.raises(FetchDeliveryFileTagsError):
        tag_fetcher.fetch_tags(unsupported_workflow)
