from cg.meta.workflow.mutant.metadata_parser import MetadataParser
from cg.store.models import Case

from cg.store.database import initialize_database
from cg.store.store import Store


initialize_database("mysql+pymysql://produser:jqBRnwAM7wvq3wVLaP-K@127.0.0.1:19002/cg")
status_db = Store()


def test_parse_metadata():
    # GIVEN a case object
    case: Case = status_db.get_case_by_internal_id("lovingfeline")

    # WHEN parsing the metadata
    MetadataParser.parse_metadata(case)

    # THEN no error is thrown


# TODO: Is it necessary to test these functions separately?
# Particularly parse_metadata_for_internal_negative_control fetches information from LIMS as well.


def test_parse_metadata_for_case():
    # GIVEN a case object
    case: Case = status_db.get_case_by_internal_id("lovingfeline")

    # WHEN parsing the metadata
    MetadataParser.parse_metadata_for_case(case)

    # THEN no error is thrown


# How to initialise the lims api?
# parse_metadata_for_internal_negative_control(
#    self, metadata_for_case: SamplesMetadataMetrics
# ) -> dict[str, SampleMetadata]:
