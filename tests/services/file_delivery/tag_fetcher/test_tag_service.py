"""Module to test fetching of file tags for delivery."""

import pytest

from cg.constants import Workflow
from cg.constants.delivery import PIPELINE_ANALYSIS_TAG_MAP
from cg.services.deliver_files.tag_fetcher.exc import FetchDeliveryFileTagsError
from cg.services.deliver_files.tag_fetcher.fohm_upload_service import FOHMUploadTagsFetcher
from cg.services.deliver_files.tag_fetcher.models import DeliveryFileTags
from cg.services.deliver_files.tag_fetcher.sample_and_case_service import (
    SampleAndCaseDeliveryTagsFetcher,
)


@pytest.mark.parametrize(
    "workflow",
    [
        Workflow.BALSAMIC,
        Workflow.BALSAMIC_UMI,
        Workflow.MIP_DNA,
        Workflow.MIP_RNA,
        Workflow.MICROSALT,
        Workflow.NALLO,
        Workflow.RAREDISEASE,
        Workflow.RAW_DATA,
        Workflow.RNAFUSION,
        Workflow.TAXPROFILER,
        Workflow.TOMTE,
    ],
)
def test_fetch_tags(workflow: Workflow):
    """Test to fetch tags for the files to deliver."""
    # GIVEN a workflow and a tag fetcher
    tag_fetcher = SampleAndCaseDeliveryTagsFetcher()

    # WHEN fetching the tags for the files to deliver
    tags: DeliveryFileTags = tag_fetcher.fetch_tags(workflow)

    # THEN assert that the tags are fetched
    assert tags.case_tags == PIPELINE_ANALYSIS_TAG_MAP[workflow]["case_tags"]
    assert tags.sample_tags == PIPELINE_ANALYSIS_TAG_MAP[workflow]["sample_tags"]


def test_fetch_tags_unsupported_workflow():
    """Test to fetch tags for the files to deliver."""
    # GIVEN an unsupported workflow and a tag fetcher
    unsupported_workflow: str = "workflow_not_supported"
    tag_fetcher = SampleAndCaseDeliveryTagsFetcher()

    # WHEN fetching the tags for the files to deliver

    # THEN a FetchDeliveryFileTagsError should be raised
    with pytest.raises(FetchDeliveryFileTagsError):
        tag_fetcher.fetch_tags(unsupported_workflow)


def test_fohm_upload_tags_fetcher():
    # GIVEN a tag fetcher
    test_fetcher = FOHMUploadTagsFetcher()

    # WHEN fetching the tags for the files to deliver
    tags: DeliveryFileTags = test_fetcher.fetch_tags(Workflow.MUTANT)

    # THEN assert that the tags are fetched
    assert tags.case_tags is None
    assert tags.sample_tags == [{"consensus-sample"}, {"vcf-report"}]
