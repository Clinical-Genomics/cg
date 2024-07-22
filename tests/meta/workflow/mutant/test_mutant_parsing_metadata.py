from cg.meta.workflow.mutant.metadata_parser.metadata_parser import MetadataParser
from cg.store.models import Case
from cg.store.store import Store
from tests.mocks.limsmock import MockLimsAPI


def test_parse_metadata(mutant_store: Store, mutant_lims: MockLimsAPI):
    # GIVEN a case object
    case: Case = mutant_store.get_case_by_internal_id("case_qc_pass")

    # WHEN parsing the metadata
    MetadataParser(status_db=mutant_store, lims=mutant_lims).parse_metadata(case=case)

    # THEN no error is thrown
