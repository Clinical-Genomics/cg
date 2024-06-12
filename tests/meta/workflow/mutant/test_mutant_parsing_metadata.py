from cg.meta.workflow.mutant.metadata_parser.metadata_parser import MetadataParser
from cg.store.models import Case


def test_parse_metadata(mutant_store, mutant_lims):
    # GIVEN a case object
    case: Case = mutant_store.get_case_by_internal_id("mutant_case_qc_pass")

    # WHEN parsing the metadata
    MetadataParser(status_db=mutant_store, lims=mutant_lims).parse_metadata(case=case)

    # THEN no error is thrown


def test_parse_metadata_for_case(mutant_store, mutant_lims):
    # GIVEN a case object
    case: Case = mutant_store.get_case_by_internal_id("mutant_case_qc_pass")

    # WHEN parsing the metadata
    MetadataParser(status_db=mutant_store, lims=mutant_lims).parse_metadata_for_case(case=case)

    # THEN no error is thrown


def test_parse_metadata_for_internal_negative_control(mutant_store, mutant_lims):
    # GIVEN a SamplesMetadataMetrics object
    metadata_parser = MetadataParser(status_db=mutant_store, lims=mutant_lims)
    case: Case = mutant_store.get_case_by_internal_id("mutant_case_qc_pass")
    metadata_for_case_qc_pass = metadata_parser.parse_metadata_for_case(case=case)

    # WHEN parsing the metadata
    metadata_parser.parse_metadata_for_internal_negative_control(metadata_for_case_qc_pass)

    # THEN no error is thrown
