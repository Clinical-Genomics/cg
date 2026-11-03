from http import HTTPStatus
from typing import Generator

import pytest
from flask import Flask
from flask.testing import FlaskClient
from pytest_mock import MockerFixture

from cg.constants.devices import DeviceType, RevioNames
from cg.server.admin import BaseView
from cg.server.ext import admin
from cg.server.ext import db as store
from cg.services.run_devices.pacbio.data_transfer_service.dto import (
    PacBioSampleSequencingMetricsDTO,
    PacBioSequencingRunDTO,
)
from cg.store.models import (
    Case,
    IlluminaFlowCell,
    IlluminaSequencingRun,
    PacbioSequencingRun,
    PacbioSMRTCellMetrics,
    RunDevice,
)
from tests.store_helpers import StoreHelpers


@pytest.fixture
def admin_client(app: Flask, mocker: MockerFixture) -> Generator[FlaskClient, None, None]:
    # Bypass the Google login of the admin views
    mocker.patch.object(BaseView, "is_accessible", return_value=True)

    # The admin views keep the database session from when they were created, use the test session
    for view in admin._views:
        if isinstance(view, BaseView):
            mocker.patch.object(view, "session", store.session)

    yield app.test_client()


def test_export_selected_cases(admin_client: FlaskClient, helpers: StoreHelpers):
    # GIVEN three cases in the database
    selected_case: Case = helpers.add_case(store=store, internal_id="selected", name="selected")
    other_selected_case: Case = helpers.add_case(
        store=store, internal_id="other_selected", name="other_selected"
    )
    helpers.add_case(store=store, internal_id="not_selected", name="not_selected")

    # WHEN exporting with two of the cases selected
    response = admin_client.get(
        "/admin/case/export/csv/",
        query_string={"selected_id": [selected_case.id, other_selected_case.id]},
    )

    # THEN the export is successful
    assert response.status_code == HTTPStatus.OK

    # THEN only the selected cases are exported
    exported_csv: str = response.get_data(as_text=True)
    assert len(exported_csv.splitlines()) == 3  # Header + two selected cases
    assert "not_selected" not in exported_csv


def test_export_without_selected_cases_exports_all(
    admin_client: FlaskClient, helpers: StoreHelpers
):
    # GIVEN three cases in the database
    for name in ["first", "second", "third"]:
        helpers.add_case(store=store, internal_id=name, name=name)

    # WHEN exporting without any cases selected
    response = admin_client.get("/admin/case/export/csv/")

    # THEN the export is successful
    assert response.status_code == HTTPStatus.OK

    # THEN all cases are exported
    exported_csv: str = response.get_data(as_text=True)
    assert len(exported_csv.splitlines()) == 4  # Header + three cases


def test_export_column_only_shown_through_formatter(
    admin_client: FlaskClient, helpers: StoreHelpers
):
    # GIVEN an Illumina sequencing run, whose internal id is only shown through a column formatter
    flow_cell: IlluminaFlowCell = helpers.add_illumina_flow_cell(
        store=store, flow_cell_id="HVKJCDRXX", model="10B"
    )
    helpers.add_illumina_sequencing_run(store=store, flow_cell=flow_cell)

    # WHEN exporting the Illumina sequencing runs
    response = admin_client.get("/admin/illuminasequencingrun/export/csv/")

    # THEN the export is successful
    assert response.status_code == HTTPStatus.OK

    # THEN the internal id and model of the flow cell are exported as plain text
    exported_row: str = response.get_data(as_text=True).splitlines()[1]
    assert exported_row.startswith("HVKJCDRXX,10B,")


@pytest.fixture
def pacbio_smrt_cell_internal_id() -> str:
    return "EA094834"


@pytest.fixture
def pacbio_sample_sequencing_metrics(pacbio_smrt_cell_internal_id: str, helpers: StoreHelpers):
    """Add a PacBio SMRT cell with metrics for a sample to the store."""
    smrt_cell: RunDevice = helpers.add_run_device(
        store=store, id=1, type=DeviceType.PACBIO, internal_id=pacbio_smrt_cell_internal_id
    )
    sequencing_run: PacbioSequencingRun = store.create_pacbio_sequencing_run(
        pacbio_sequencing_run_dto=PacBioSequencingRunDTO(
            instrument_name=RevioNames.BETTY,
            run_id="r84202_20240913_121403",
            run_name="run-name",
            unique_id="unique-id",
        )
    )
    smrt_cell_metrics: PacbioSMRTCellMetrics = helpers.add_pacbio_smrt_cell_metrics(
        store=store, id=1, device_id=smrt_cell.id, sequencing_run=sequencing_run
    )
    helpers.add_sample(store=store, internal_id="ACC123")
    store.create_pac_bio_sample_sequencing_run(
        sample_run_metrics_dto=PacBioSampleSequencingMetricsDTO(
            sample_internal_id="ACC123",
            hifi_reads=100,
            hifi_yield=1000,
            hifi_mean_read_length=10,
            hifi_median_read_quality="Q30",
            polymerase_mean_read_length=10,
        ),
        smrt_cell_metrics=smrt_cell_metrics,
    )
    store.commit_to_store()


@pytest.mark.parametrize("table", ["pacbiosmrtcellmetrics", "pacbiosamplesequencingmetrics"])
def test_export_pacbio_smrt_cell_id_only_shown_through_formatter(
    table: str,
    admin_client: FlaskClient,
    pacbio_sample_sequencing_metrics,
    pacbio_smrt_cell_internal_id: str,
):
    # GIVEN PacBio metrics, whose SMRT cell internal id is only shown through a column formatter

    # WHEN exporting the PacBio table
    response = admin_client.get(f"/admin/{table}/export/csv/")

    # THEN the export is successful
    assert response.status_code == HTTPStatus.OK

    # THEN the SMRT cell internal id is exported as plain text in the first column
    exported_row: str = response.get_data(as_text=True).splitlines()[1]
    assert exported_row.startswith(f"{pacbio_smrt_cell_internal_id},")


def test_export_illumina_sample_metrics_flow_cell_only_shown_through_formatter(
    admin_client: FlaskClient, helpers: StoreHelpers
):
    # GIVEN Illumina sample metrics, whose flow cell is only shown through a column formatter
    flow_cell: IlluminaFlowCell = helpers.add_illumina_flow_cell(
        store=store, flow_cell_id="HVKJCDRXX"
    )
    sequencing_run: IlluminaSequencingRun = helpers.add_illumina_sequencing_run(
        store=store, flow_cell=flow_cell
    )
    helpers.add_sample(store=store, internal_id="ACC123")
    helpers.add_illumina_sample_sequencing_metrics_object(
        store=store, sample_id="ACC123", sequencing_run=sequencing_run, lane=1
    )

    # WHEN exporting the Illumina sample metrics
    response = admin_client.get("/admin/illuminasamplesequencingmetrics/export/csv/")

    # THEN the export is successful
    assert response.status_code == HTTPStatus.OK

    # THEN the flow cell internal id is exported as plain text in the first column
    exported_row: str = response.get_data(as_text=True).splitlines()[1]
    assert exported_row.startswith("HVKJCDRXX,")
