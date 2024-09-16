from cg.constants import Workflow
from cg.services.deliver_files.delivery_file_tag_fetcher_service.delivery_file_tag_fetcher_service import (
    FetchDeliveryFileTagsService,
)
from cg.services.deliver_files.delivery_file_tag_fetcher_service.error_handling import (
    handle_tag_errors,
)
from cg.services.deliver_files.delivery_file_tag_fetcher_service.models import DeliveryFileTags


class BamDeliveryFileTagsFetcher(FetchDeliveryFileTagsService):
    """Class to fetch tags for bam files to deliver."""

    @handle_tag_errors
    def fetch_tags(self, workflow: Workflow) -> DeliveryFileTags:
        """Fetch the tags for the bam files to deliver."""
        return DeliveryFileTags(
            case_tags=None,
            sample_tags=["bam"],
        )

    @staticmethod
    def _validate_workflow(workflow: Workflow):
        """Validate the workflow."""
        if not workflow == Workflow.FASTQ:
            raise ValueError(f"Workflow {workflow} is not supported for only BAM file delivery.")
        return workflow
