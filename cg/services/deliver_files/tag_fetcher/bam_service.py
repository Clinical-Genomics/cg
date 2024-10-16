from cg.constants import Workflow
from cg.constants.housekeeper_tags import AlignmentFileTag
from cg.services.deliver_files.tag_fetcher.abstract import (
    FetchDeliveryFileTagsService,
)
from cg.services.deliver_files.tag_fetcher.error_handling import (
    handle_tag_errors,
)
from cg.services.deliver_files.tag_fetcher.models import DeliveryFileTags


class BamDeliveryTagsFetcher(FetchDeliveryFileTagsService):
    """Class to fetch tags for bam files to deliver."""

    @handle_tag_errors
    def fetch_tags(self, workflow: Workflow) -> DeliveryFileTags:
        """Fetch the tags for the bam files to deliver."""
        self._validate_workflow(workflow=workflow)
        return DeliveryFileTags(
            case_tags=None,
            sample_tags=[{AlignmentFileTag.BAM}],
        )

    @staticmethod
    def _validate_workflow(workflow: Workflow):
        """Validate the workflow."""
        if workflow != Workflow.RAW_DATA:
            raise ValueError(f"Workflow {workflow} is not supported for only BAM file delivery.")
        return workflow
