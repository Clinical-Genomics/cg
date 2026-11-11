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
    # file_types + case_id -> case files in housekeeper
    # for sample in case.samples:
    #   file_types + sample_id -> sample files in housekeeper
    # Create ticket dir on caesar
    # Create case dir
    # Create sample dir
    #

    pass
