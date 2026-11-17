import os
from pathlib import Path

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


def _link_analysis_files(
    analysis: Analysis, housekeeper_api: HousekeeperAPI, status_db: Store, base_delivery_path: Path
):
    case: Case = analysis.case

    # file_types + case_id -> case files in housekeeper
    upload_keys: list[UploadKeys] = status_db.get_upload_keys(
        workflow=case.data_analysis, upload_to_customer_inbox=True
    )
    file_types: list[str] = [key.file_type for key in upload_keys]
    files: list[File] = housekeeper_api.files(
        file_types=file_types, version=analysis.housekeeper_version_id
    ).all()

    # create case dir using the case name in ticket dir if non-existent
    case_delivery_directory = Path(
        base_delivery_path, case.customer.internal_id, "inbox", analysis.order.ticket_id, case.name
    )
    case_delivery_directory.mkdir(parents=True, exist_ok=True)

    replacements: dict = {
        case.internal_id: case.name,
        **{sample.id: sample.name for sample in case.samples},
    }
    for file in files:
        # TODO change this because it will cause trouble in the renaming
        new_name = file.path.translate(str.maketrans(replacements))
        os.link(src=file.full_path, dst=Path(case_delivery_directory, new_name))

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
