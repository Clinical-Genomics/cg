from housekeeper.store.models import File

from cg.apps.housekeeper.hk import HousekeeperAPI
from cg.constants import Workflow
from cg.store.models import Analysis, Case, UploadKeys
from cg.store.store import Store


def upload_results(analysis: Analysis, status_db: Store):
    # TODO: implement logic for determine where to upload the analysis.
    pass


def _upload():
    pass


def _upload_to_scout():
    pass


def _upload_to_loqus_db():
    pass


def _upload_to_chanjo():
    pass


def _upload_to_customer_inbox(
    analysis: Analysis, housekeeper_api: HousekeeperAPI, status_db: Store
):
    # Take a case id as input
    # Case id -> customer
    # Case id -> workflow
    # Case id -> data delivery
    # Workflow -> File_types

    # Create ticket dir on caesar
    _link_analysis_files(analysis=analysis, housekeeper_api=housekeeper_api, status_db=status_db)
    _link_raw_data()
    # Rsync case and samples dir to Caesar


def _link_analysis_files(analysis: Analysis, housekeeper_api: HousekeeperAPI, status_db: Store):
    case: Case = analysis.case

    # file_types + case_id -> case files in housekeeper
    upload_keys: list[UploadKeys] = status_db.get_upload_keys(
        workflow=case.data_analysis, upload_to_customer_inbox=True
    )
    file_types: list[str] = [key.file_type for key in upload_keys]
    case_files: list[File] = housekeeper_api.get_files_from_file_types(
        file_types=file_types, version_id=analysis.housekeeper_version_id, tags={case.internal_id}
    )

    # create case dir using the case name in ticket dir if non-existent

    # Rename and link case files

    for sample in case.samples:
        #   create sample dir with sample name in ticket dir if non-existent

        #   file_types + sample_id -> sample analysis files in housekeeper
        sample_files: list[File] = housekeeper_api.get_files_from_file_types(
            file_types=file_types,
            version_id=analysis.housekeeper_version_id,
            tags={sample.internal_id},
        )

    #   Rename and link sample files


def _link_raw_data():
    # for sample in case.samples:
    #   create sample dir with sample name in ticket dir if non-existent
    #   Get sample raw data from sample bundle
    pass
