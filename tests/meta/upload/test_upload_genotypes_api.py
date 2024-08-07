"""Tests for the upload genotypes api"""

import pytest
from _pytest.fixtures import FixtureRequest

from datetime import datetime
from pathlib import Path

from cg.meta.workflow.analysis import AnalysisAPI
from cg.meta.workflow.balsamic import BalsamicAnalysisAPI
from cg.meta.workflow.mip_dna import MipDNAAnalysisAPI
from cg.meta.workflow.raredisease import RarediseaseAnalysisAPI
from cg.meta.upload.gt import UploadGenotypesAPI
from cg.models.cg_config import CGConfig
from cg.models.deliverables.metric_deliverables import MetricsBase
from cg.models.mip.mip_metrics_deliverables import MIPMetricsDeliverables
from cg.store.models import Analysis


def test_get_analysis_sex_mip(
    case_qc_metrics_deliverables: Path,
    genotype_analysis_sex: dict,
):
    """Test to get the predicted sex from a MIP run using the upload genotypes API"""
    # GIVEN an AnalysisAPI and some qcmetrics data

    # WHEN fetching the predicted sex by the analysis
    sex: dict = MipDNAAnalysisAPI._get_analysis_sex(qc_metrics_file=case_qc_metrics_deliverables)

    # THEN assert that the the predicted sex per sample_id is returned
    assert sex == genotype_analysis_sex


def test_get_analysis_sex_raredisease(
    case_qc_metrics_deliverables: Path,
    genotype_analysis_sex: dict,
):
    """Test to get the predicted sex from a MIP run using the upload genotypes API"""
    # GIVEN an AnalysisAPI and some qcmetrics data

    # WHEN fetching the predicted sex by the analysis
    sex: dict = RarediseaseAnalysisAPI._get_analysis_sex(
        qc_metrics_file=case_qc_metrics_deliverables
    )

    # THEN assert that the the predicted sex per sample_id is returned
    assert sex == genotype_analysis_sex


def test_get_parsed_qc_metrics_data_mip(case_qc_metrics_deliverables: Path):
    """Test to get the predicted sex from a MIP run using the upload genotypes API"""
    # GIVEN an AnalysisAPI and qcmetrics data

    # WHEN fetching the predicted sex
    metrics_object = MipDNAAnalysisAPI._get_parsed_qc_metrics_data(case_qc_metrics_deliverables)

    # THEN assert that it was successfully created
    assert isinstance(metrics_object, MIPMetricsDeliverables)


def test_get_parsed_qc_metrics_data_raredisease(case_qc_metrics_deliverables: Path):
    """Test to get the predicted sex from a RAREDISEASE run using the upload Genotypes API"""
    # GIVEN an AnalysisAPI and some qcmetrics data

    # WHEN fetching the predicted sex
    metrics_object: list[MetricsBase] = RarediseaseAnalysisAPI._get_parsed_qc_metrics_data(
        case_qc_metrics_deliverables
    )

    def is_list_of_metricsbase(obj):
        if isinstance(obj, list):
            return all(isinstance(item, MetricsBase) for item in obj)
        return False

    # THEN assert that it was successfully created
    assert is_list_of_metricsbase(metrics_object)


def test_get_bcf_file_mip(
    upload_genotypes_api: UploadGenotypesAPI,
    case_id: str,
    cg_context: CGConfig,
    timestamp: datetime,
):
    """Test to get the predicted sex from a MIP run using the upload genotypes API"""
    # GIVEN a UploadGenotypesAPI populated with some data in housekeeper
    analysis_api = MipDNAAnalysisAPI(config=cg_context)
    hk_version = upload_genotypes_api.hk.version(case_id, timestamp)

    # WHEN fetching the gbcf file with the api
    gbcf = analysis_api.get_bcf_file(hk_version_obj=hk_version)
    # THEN assert that the file has the correct tag
    assert "snv-gbcf" in (tag.name for tag in gbcf.tags)


def test_get_bcf_file_raredisease(
    upload_genotypes_api: UploadGenotypesAPI,
    case_id: str,
    timestamp: datetime,
):
    """Test to get the predicted sex from a RAREDISEASE run using the upload genotypes API"""
    # GIVEN a UploadGenotypeAPI populated with some data
    hk_version = upload_genotypes_api.hk.version(case_id, timestamp)

    analysis_api: AnalysisAPI = MipDNAAnalysisAPI

    # WHEN fetching the gbcf file with the api
    gbcf = analysis_api.get_bcf_file(hk_version_obj=hk_version)

    # THEN assert that the file has the correct tag
    assert "snv-gbcf" in (tag.name for tag in gbcf.tags)


def test_get_data(
    analysis_obj: Analysis,
    genotype_analysis_sex: dict,
    mocker,
    upload_genotypes_api: UploadGenotypesAPI,
):
    """Test to get data from the UploadGenotypesAPI"""
    # GIVEN a UploadGenotypeAPI populated with some data

    # GIVEN analysis sex were generated and could be found
    mocker.patch.object(UploadGenotypesAPI, "analysis_sex")
    UploadGenotypesAPI.analysis_sex.return_value = genotype_analysis_sex

    # WHEN parsing the data
    result = upload_genotypes_api.data(analysis=analysis_obj)

    # THEN assert that the result looks like expected
    assert len(result["samples_sex"]) == 3
