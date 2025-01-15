from cg.constants import Workflow, SequencingFileTag
from cg.services.deliver_files.tag_fetcher.abstract import FetchDeliveryFileTagsService
from cg.services.deliver_files.tag_fetcher.error_handling import handle_tag_errors
from cg.services.deliver_files.tag_fetcher.models import DeliveryFileTags


class FOHMUploadTagsFetcher(FetchDeliveryFileTagsService):
    """Class to fetch tags for FOHM upload files."""

    @handle_tag_errors
    def fetch_tags(self, workflow: Workflow) -> DeliveryFileTags:
        """
        Fetch the tags for the bam files to deliver.
        NOTE: workflow raw data here is required to fit the implementation of the raw data delivery file fetcher.
        if workflow is MUTANT, return tags for consensus-sample and vcf-report to fetch sample files from the case bundle.
        if workflow is RAW_DATA, return tags for fastq to fetch fastq files from the sample bundle.
        Required since some of the sample specific files are stored on the case bundle, but also fastq files.
        Not separating these would cause fetching of case bundle fastq files if present.

        Hardcoded to only return the tags for the files to deliver.
        args:
            workflow: Workflow: The workflow to fetch tags
        """
        self._validate_workflow(workflow=workflow)
        return (
            DeliveryFileTags(
                case_tags=None,
                sample_tags=[{"consensus-sample"}, {"vcf-report"}],
            )
            if workflow == Workflow.MUTANT
            else DeliveryFileTags(
                case_tags=None,
                sample_tags=[{SequencingFileTag.FASTQ}],
            )
        )

    @staticmethod
    def _validate_workflow(workflow: Workflow):
        """
        Validate the workflow.
        NOTE: workflow raw data here is required to fit the implementation of the raw data delivery file fetcher.
        args:
            workflow: Workflow: The workflow to validate.
        """
        if workflow not in [Workflow.MUTANT, Workflow.RAW_DATA]:
            raise ValueError(f"Workflow {workflow} is not supported for FOHM upload file delivery.")
        return workflow
