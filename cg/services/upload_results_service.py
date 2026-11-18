import os
from pathlib import Path
from typing import Any

from housekeeper.store.models import File

from cg.apps.housekeeper.hk import HousekeeperAPI
from cg.services.deliver_files.rsync.service import DeliveryRsyncService
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
    # Add RSYNC analysis to Trailblazer
    # Potentially: write trailblazer config file if needed
    # Add upload job to the new rsync trailblazer analysis
    # Add upload job to the main trailblazer analysis


def _link_analysis_files(
    analysis: Analysis,
    housekeeper_api: HousekeeperAPI,
    rsync_service: DeliveryRsyncService,
    status_db: Store,
    base_delivery_path: Path,
):
    case: Case = analysis.case
    case_delivery_directory = Path(
        base_delivery_path,
        case.customer.internal_id,
        "inbox",
        str(analysis.order.ticket_id),
        case.name,
    )
    case_delivery_directory.mkdir(parents=True, exist_ok=True)

    upload_keys: list[UploadKeys] = status_db.get_upload_keys(
        workflow=case.data_analysis, upload_to_customer_inbox=True
    )
    file_types: list[str] = [key.file_type for key in upload_keys]

    # get File objects from HK
    files: list[File] = housekeeper_api.files(
        file_types=file_types, version=analysis.housekeeper_version_id
    ).all()
    # for every file, get path and full path
    # for each file, link to customer directory in hasta
    for file in files:
        source_path = Path(file.full_path)
        os.link(src=source_path, dst=Path(case_delivery_directory, source_path.name))
    # rsync the directory to caesar
    rsync_service.run_rsync_for_analysis()

    # case_files: list[File] = housekeeper_api.files(
    #     file_types=file_types, version=analysis.housekeeper_version_id, tags={case.internal_id}
    # ).all()
    # replacements: dict = {
    #     case.internal_id: case.name,
    # }
    # _rename_and_link_files(
    #     case_delivery_directory=case_delivery_directory, files=case_files, replacements=replacements
    # )

    # for sample in case.samples:
    #     sample_files: list[File] = housekeeper_api.files(
    #         bundle=case.internal_id,
    #         file_types=file_types,
    #         version=analysis.housekeeper_version_id,
    #         tags={sample.internal_id},
    #     ).all()
    #     sample_replacements = {sample.internal_id: sample.name, **replacements}
    #     _rename_and_link_files(
    #         case_delivery_directory=case_delivery_directory,
    #         files=sample_files,
    #         replacements=sample_replacements,
    #     )


def _rename_and_link_files(
    case_delivery_directory: Any, files: list[File], replacements: dict[Any, Any]
):
    for file in files:
        new_name = file.path.translate(str.maketrans(replacements))
        os.link(src=file.full_path, dst=Path(case_delivery_directory, new_name))


def _link_raw_data():
    # for sample in case.samples:
    #   create sample dir with sample name in ticket dir if non-existent
    #   Get sample raw data from sample bundle
    pass
