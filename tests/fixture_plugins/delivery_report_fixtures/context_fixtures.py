"""Delivery report CG context fixtures."""

from datetime import datetime
from pathlib import Path

import pytest
from pytest_mock import MockFixture

from cg.apps.lims import LimsAPI
from cg.clients.chanjo2.models import CoverageMetrics
from cg.constants import Workflow, DataDelivery
from cg.meta.delivery_report.raredisease import RarediseaseDeliveryReportAPI
from cg.meta.workflow.analysis import AnalysisAPI
from cg.meta.workflow.nf_analysis import NfAnalysisAPI
from cg.meta.workflow.raredisease import RarediseaseAnalysisAPI
from cg.models.cg_config import CGConfig
from cg.models.delivery_report.report import ScoutVariantsFiles
from cg.store.models import Case, Sample
from cg.store.store import Store
from tests.conftest import raredisease_case_id
from tests.store_helpers import StoreHelpers


@pytest.fixture
def raredisease_delivery_report_store_context(
    raredisease_case_id: str,
    sample_id: str,
    wgs_application_tag: str,
    total_sequenced_reads_pass: int,
    ticket_id: str,
    base_store: Store,
    helpers: StoreHelpers,
) -> Store:
    """Raredisease delivery report Statusdb fixture."""

    case: Case = helpers.add_case(
        store=base_store,
        internal_id=raredisease_case_id,
        name=raredisease_case_id,
        data_analysis=Workflow.RAREDISEASE,
    )

    sample: Sample = helpers.add_sample(
        store=base_store,
        internal_id=sample_id,
        last_sequenced_at=datetime.now(),
        received_at=datetime.now(),
        reads=total_sequenced_reads_pass,
        application_tag=wgs_application_tag,
        original_ticket=ticket_id,
    )

    helpers.add_relationship(base_store, case=case, sample=sample)

    helpers.add_analysis(
        store=base_store,
        case=case,
        started_at=datetime.now(),
        completed_at=datetime.now(),
        workflow=Workflow.RAREDISEASE,
        data_delivery=DataDelivery.ANALYSIS_SCOUT,
    )

    return base_store


@pytest.fixture
def raredisease_delivery_report_context(
    cg_context: CGConfig,
    raredisease_delivery_report_store_context: Store,
    raredisease_multiqc_json_metrics_path: Path,
    lims_samples: list[dict],
    library_prep_method: str,
    libary_sequencing_method: str,
    capture_kit: str,
    coverage_metrics: CoverageMetrics,
    scout_variants_files: ScoutVariantsFiles,
    mocker: MockFixture,
) -> CGConfig:
    """Raredisease context for the delivery report generation."""

    # CG context
    cg_context.status_db_ = raredisease_delivery_report_store_context
    cg_context.meta_apis["analysis_api"] = RarediseaseAnalysisAPI(config=cg_context)

    # Mocked methods
    mocker.patch.object(
        NfAnalysisAPI, "get_multiqc_json_path", return_value=raredisease_multiqc_json_metrics_path
    )  # RD specific
    mocker.patch.object(LimsAPI, "sample", return_value=lims_samples[0])
    mocker.patch.object(LimsAPI, "get_prep_method", return_value=library_prep_method)
    mocker.patch.object(LimsAPI, "get_sequencing_method", return_value=libary_sequencing_method)
    mocker.patch.object(LimsAPI, "capture_kit", return_value=capture_kit)
    mocker.patch.object(AnalysisAPI, "get_gene_ids_from_scout", return_value=[])  # RD specific
    mocker.patch.object(
        RarediseaseAnalysisAPI, "get_sample_coverage", return_value=coverage_metrics
    )  # RD specific
    mocker.patch.object(
        RarediseaseDeliveryReportAPI, "get_scout_variants_files", return_value=scout_variants_files
    )  # RD specific
    return cg_context
