from cg.store.models import Case
from cg.store.store import Store


def upload_results(case_id: str, status_db: Store):
    case: Case = status_db.get_case_by_internal_id_strict(internal_id=case_id)
    functions = choose_where_to_upload(case_id)
    _upload(list_of_functions=functions)


def _upload():
    pass


def _upload_to_scout():
    pass


def _upload_to_loqus_db():
    pass


def _upload_to_chanjo():
    pass


def _upload_to_customer_inbox():
    # Take a case id as input
    # Case id -> customer
    # Case id -> workflow
    # Case id -> Case delivery
    # Workflow -> File_types
    # Create ticket dir on caesar
    #

    pass


def _link_analysis_files():
    # file_types + case_id -> case files in housekeeper
    # create case dir using the case name in ticket dir if non-existent
    # Rename and link case files
    # for sample in case.samples:
    #   create sample dir with sample name in ticket dir if non-existent
    #   file_types + sample_id -> sample analysis files in housekeeper
    # .  Rename and link sample files
    pass


def _link_raw_data():
    # for sample in case.samples:
    #   create sample dir with sample name in ticket dir if non-existent
    #   Get sample raw data from sample bundle
    pass
