from cg.meta.workflow.mutant.metadata_parser import MetadataParser
from cg.store.models import Case


def test_parse_metadata(case: Case):
    # GIVEN a case object

    # WHEN parsing the metadata
    MetadataParser.parse_metadata(case)

    # THEN no error is thrown


# TODO: Is it necessary to test these functions separately?
# Particularly parse_metadata_for_internal_negative_control fetches information from LIMS as well.

# parse_metadata_for_case(self, case: Case) -> dict[str, SampleMetadata]:

# parse_metadata_for_internal_negative_control(
#    self, metadata_for_case: SamplesMetadataMetrics
# ) -> dict[str, SampleMetadata]:
