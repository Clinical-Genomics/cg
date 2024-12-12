from cg.constants import Workflow
from cg.constants.housekeeper_tags import SequencingFileTag
from cg.services.deliver_files.tag_fetcher.abstract import FetchDeliveryFileTagsService
from cg.services.deliver_files.tag_fetcher.error_handling import handle_tag_errors
from cg.services.deliver_files.tag_fetcher.models import DeliveryFileTags


class FOHMUploadTagsFetcher(FetchDeliveryFileTagsService):
    """Class to fetch tags for FOHM upload files."""

    @handle_tag_errors
    def fetch_tags(self, workflow: Workflow) -> DeliveryFileTags:
        """Fetch the tags for the bam files to deliver."""
        self._validate_workflow(workflow=workflow)
        return DeliveryFileTags(
            case_tags=[{"fohm-delivery"}],
            sample_tags=[{SequencingFileTag.FASTQ}],
        )

    @staticmethod
    def _validate_workflow(workflow: Workflow):
        """
        Validate the workflow.
        NOTE: workflow raw data here is required to fit the implementation of the raw data delivery file fetcher.
        """
        if workflow != Workflow.MUTANT or workflow != Workflow.RAW_DATA:
            raise ValueError(f"Workflow {workflow} is not supported for FOHM upload file delivery.")
        return workflow
