"""Delivery report CG context fixtures."""

from datetime import datetime
from pathlib import Path

import click
import pytest
from pytest_mock import MockFixture

from cg.apps.lims import LimsAPI
from cg.cli.generate.delivery_report.base import generate_delivery_report
from cg.clients.chanjo2.models import CoverageMetrics
from cg.constants import DataDelivery, Workflow
from cg.meta.delivery_report.delivery_report_api import DeliveryReportAPI
from cg.meta.delivery_report.raredisease import RarediseaseDeliveryReportAPI
from cg.meta.delivery_report.rnafusion import RnafusionDeliveryReportAPI
from cg.meta.workflow.analysis import AnalysisAPI
from cg.meta.workflow.nf_analysis import NfAnalysisAPI
from cg.meta.workflow.raredisease import RarediseaseAnalysisAPI
from cg.meta.workflow.rnafusion import RnafusionAnalysisAPI
from cg.models.cg_config import CGConfig
from cg.models.delivery_report.report import ScoutVariantsFiles
from cg.store.models import Case, Sample
from cg.store.store import Store
from tests.conftest import raredisease_case_id
from tests.store_helpers import StoreHelpers


@pytest.fixture
def delivery_report_context(
    capture_kit: str,
    cg_context: CGConfig,
    libary_sequencing_method: str,
    library_prep_method: str,
    lims_samples: list[dict],
    mocker: MockFixture,
) -> CGConfig:
    """Delivery report generation context."""
    mocker.patch.object(AnalysisAPI, "get_gene_ids_from_scout", return_value=[])
    mocker.patch.object(DeliveryReportAPI, "get_delivery_report_from_hk", return_value=None)
    mocker.patch.object(LimsAPI, "sample", return_value=lims_samples[0])
    mocker.patch.object(LimsAPI, "get_prep_method", return_value=library_prep_method)
    mocker.patch.object(LimsAPI, "get_sequencing_method", return_value=libary_sequencing_method)
    mocker.patch.object(LimsAPI, "capture_kit", return_value=capture_kit)
    mocker.patch.object(LimsAPI, "get_sample_dv200", return_value=75.0)
    mocker.patch.object(LimsAPI, "get_latest_rna_input_amount", return_value=300.0)
    mocker.patch.object(LimsAPI, "get_sample_rin", return_value=10)
    return cg_context


@pytest.fixture
def raredisease_delivery_report_store_context(
    base_store: Store,
    helpers: StoreHelpers,
    raredisease_case_id: str,
    sample_id: str,
    ticket_id: str,
    total_sequenced_reads_pass: int,
    wgs_application_tag: str,
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
        reference_genome="hg19",
    )
    helpers.add_relationship(store=base_store, case=case, sample=sample)
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
def rnafusion_delivery_report_store_context(
    base_store: Store,
    helpers: StoreHelpers,
    rnafusion_case_id: str,
    sample_id: str,
    ticket_id: str,
    total_sequenced_reads_pass: int,
    wts_application_tag: str,
) -> Store:
    """Rnafusion delivery report Statusdb fixture."""
    case: Case = helpers.add_case(
        store=base_store,
        internal_id=rnafusion_case_id,
        name=rnafusion_case_id,
        data_analysis=Workflow.RNAFUSION,
    )
    sample: Sample = helpers.add_sample(
        store=base_store,
        internal_id=sample_id,
        last_sequenced_at=datetime.now(),
        received_at=datetime.now(),
        reads=total_sequenced_reads_pass,
        application_tag=wts_application_tag,
        original_ticket=ticket_id,
    )
    helpers.add_relationship(store=base_store, case=case, sample=sample)
    helpers.add_analysis(
        store=base_store,
        case=case,
        started_at=datetime.now(),
        completed_at=datetime.now(),
        workflow=Workflow.RNAFUSION,
        data_delivery=DataDelivery.ANALYSIS_SCOUT,
    )
    return base_store


@pytest.fixture
def raredisease_delivery_report_context(
    coverage_metrics: CoverageMetrics,
    delivery_report_context: CGConfig,
    mocker: MockFixture,
    raredisease_delivery_report_store_context: Store,
    raredisease_multiqc_json_metrics_path: Path,
    scout_variants_files: ScoutVariantsFiles,
) -> CGConfig:
    """Raredisease context for the delivery report generation."""

    # Raredisease delivery report context
    delivery_report_context.status_db_ = raredisease_delivery_report_store_context
    delivery_report_context.meta_apis["analysis_api"] = RarediseaseAnalysisAPI(
        config=delivery_report_context
    )

    # Raredisease delivery report mocked methods
    mocker.patch.object(
        NfAnalysisAPI, "get_multiqc_json_path", return_value=raredisease_multiqc_json_metrics_path
    )
    mocker.patch.object(
        RarediseaseAnalysisAPI, "get_sample_coverage", return_value=coverage_metrics
    )
    mocker.patch.object(
        RarediseaseDeliveryReportAPI, "get_scout_variants_files", return_value=scout_variants_files
    )
    return delivery_report_context


@pytest.fixture
def rnafusion_delivery_report_context(
    coverage_metrics: CoverageMetrics,
    delivery_report_context: CGConfig,
    mocker: MockFixture,
    rnafusion_delivery_report_store_context: Store,
    rnafusion_multiqc_json_metrics_path: Path,
    scout_variants_files: ScoutVariantsFiles,
) -> CGConfig:
    """Rnafusion context for the delivery report generation."""

    # Rnafusion delivery report context
    delivery_report_context.status_db_ = rnafusion_delivery_report_store_context
    delivery_report_context.meta_apis["analysis_api"] = RnafusionAnalysisAPI(
        config=delivery_report_context
    )

    # Rnafusion delivery report mocked methods
    mocker.patch.object(
        NfAnalysisAPI, "get_multiqc_json_path", return_value=rnafusion_multiqc_json_metrics_path
    )
    mocker.patch.object(
        RnafusionDeliveryReportAPI, "get_scout_variants_files", return_value=scout_variants_files
    )
    return delivery_report_context


@pytest.fixture
def raredisease_delivery_report_click_context(
    raredisease_delivery_report_context: CGConfig,
) -> click.Context:
    """Raredisease click delivery report context fixture."""
    return click.Context(generate_delivery_report, obj=raredisease_delivery_report_context)
