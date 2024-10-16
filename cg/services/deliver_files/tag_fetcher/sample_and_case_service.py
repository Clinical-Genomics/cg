from cg.constants import Workflow
from cg.constants.delivery import PIPELINE_ANALYSIS_TAG_MAP
from cg.services.deliver_files.tag_fetcher.error_handling import (
    handle_tag_errors,
)
from cg.services.deliver_files.tag_fetcher.abstract import (
    FetchDeliveryFileTagsService,
)
from cg.services.deliver_files.tag_fetcher.models import DeliveryFileTags


class SampleAndCaseDeliveryTagsFetcher(FetchDeliveryFileTagsService):

    @handle_tag_errors
    def fetch_tags(self, workflow: Workflow) -> DeliveryFileTags:
        """Get the case tags for the files that need to be delivered for a workflow."""
        self._validate_workflow(workflow)
        return DeliveryFileTags(
            case_tags=PIPELINE_ANALYSIS_TAG_MAP[workflow]["case_tags"],
            sample_tags=PIPELINE_ANALYSIS_TAG_MAP[workflow]["sample_tags"],
        )

    @staticmethod
    def _validate_workflow(workflow: Workflow):
        """Validate the workflow."""
        if workflow not in PIPELINE_ANALYSIS_TAG_MAP:
            raise ValueError(f"Workflow {workflow} is not supported.")
        return workflow
