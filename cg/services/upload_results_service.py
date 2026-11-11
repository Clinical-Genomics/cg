from cg.apps.housekeeper.hk import HousekeeperAPI
from cg.constants import Workflow
from cg.store.models import Case, UploadKeys
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


def _upload_to_customer_inbox(case: Case, housekeeper_api: HousekeeperAPI, status_db: Store):
    # Take a case id as input
    # Case id -> customer
    # Case id -> workflow
    # Case id -> data delivery
    # Workflow -> File_types

    # Create ticket dir on caesar
    _link_analysis_files(case=case, housekeeper_api=housekeeper_api, status_db=status_db)
    _link_raw_data()
    # Rsync case and samples dir to Caesar


def _link_analysis_files(case: Case, housekeeper_api: HousekeeperAPI, status_db: Store):
    # file_types + case_id -> case files in housekeeper
    upload_keys: list[UploadKeys] = status_db.get_upload_keys(
        workflow=case.data_analysis, upload_to_customer_inbox=True
    )
    # housekeeper_api.
    # create case dir using the case name in ticket dir if non-existent
    # Rename and link case files
    # for sample in case.samples:
    #   create sample dir with sample name in ticket dir if non-existent
    #   file_types + sample_id -> sample analysis files in housekeeper
    #   Rename and link sample files


def _link_raw_data():
    # for sample in case.samples:
    #   create sample dir with sample name in ticket dir if non-existent
    #   Get sample raw data from sample bundle
    pass
