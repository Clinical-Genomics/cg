"""Tests for the upload genotypes api"""

from datetime import datetime
from pathlib import Path

from cg.meta.workflow.mip_dna import MipDNAAnalysisAPI
from cg.meta.upload.gt import UploadGenotypesAPI
from cg.models.cg_config import CGConfig
from cg.models.deliverables.metric_deliverables import MetricsBase
from cg.models.mip.mip_metrics_deliverables import MIPMetricsDeliverables


def test_get_analysis_sex_mip(
    case_qc_metrics_deliverables: Path,
    genotype_analysis_sex: dict,
):
    """Test to get the predicted sex from a MIP run using the upload genotypes API"""
    # GIVEN an AnalysisAPI and some qcmetrics data

    # WHEN fetching the predicted sex by the analysis
    sex: dict = UploadGenotypesAPI.get_analysis_sex_mip_dna(self=UploadGenotypesAPI,
        qc_metrics_file=case_qc_metrics_deliverables,
    )

    # THEN assert that the the predicted sex per sample_id is returned
    assert sex == genotype_analysis_sex


# def test_get_analysis_sex_raredisease(
#     case_qc_metrics_deliverables: Path,
#     genotype_analysis_sex: dict,
# ):
#     """Test to get the predicted sex from a MIP run using the upload genotypes API"""
#     # GIVEN an analysis API

#     # WHEN fetching the predicted sex by the analysis
#     sex: dict = UploadGenotypesAPI.get_analysis_sex_raredisease(
#         qc_metrics_file=case_qc_metrics_deliverables
#     )

#     # THEN assert that the the predicted sex per sample_id is returned
#     assert sex == genotype_analysis_sex


def test_get_parsed_qc_metrics_data_mip(case_qc_metrics_deliverables: Path):
    """Test to get the predicted sex from a MIP run using the upload genotypes API"""
    # GIVEN an AnalysisAPI and qcmetrics data

    # WHEN fetching the predicted sex
    metrics_object = UploadGenotypesAPI.get_parsed_qc_metrics_data_mip_dna(
        case_qc_metrics_deliverables
    )

    # THEN assert that it was successfully created
    assert isinstance(metrics_object, MIPMetricsDeliverables)


# def test_get_parsed_qc_metrics_data_raredisease(case_qc_metrics_deliverables: Path):
#     """Test to get the predicted sex from a RAREDISEASE run using the upload Genotypes API"""
#     # GIVEN an AnalysisAPI and some qcmetrics data

#     # WHEN fetching the predicted sex
#     metrics_object: list[MetricsBase] = UploadGenotypesAPI.get_parsed_qc_metrics_data_raredisease(
#         case_qc_metrics_deliverables
#     )

#     def is_list_of_metricsbase(obj):
#         if isinstance(obj, list):
#             return all(isinstance(item, MetricsBase) for item in obj)
#         return False

#     # THEN assert that it was successfully created
#     assert is_list_of_metricsbase(metrics_object)


def test_get_bcf_file_mip(
    upload_genotypes_api: UploadGenotypesAPI,
    case_id: str,
    timestamp: datetime,
):
    """Test to get the predicted sex from a MIP run using the upload genotypes API"""
    # GIVEN a UploadGenotypesAPI populated with some data in housekeeper
    hk_version = upload_genotypes_api.hk.version(case_id, timestamp)

    # WHEN fetching the gbcf file with the api
    gbcf = upload_genotypes_api.get_bcf_file(hk_version_obj=hk_version)
    # THEN assert that the file has the correct tag
    assert "snv-gbcf" in (tag.name for tag in gbcf.tags)


# def test_get_bcf_file_raredisease(
#     upload_genotypes_api: UploadGenotypesAPI,
#     case_id: str,
#     timestamp: datetime,
# ):
#     """Test to get the predicted sex from a RAREDISEASE run using the upload genotypes API"""
#     # GIVEN a UploadGenotypeAPI populated with some data
#     hk_version = upload_genotypes_api.hk.version(case_id, timestamp)

#     # WHEN fetching the gbcf file with the api
#     gbcf = upload_genotypes_api.get_bcf_file(hk_version_obj=hk_version)

#     # THEN assert that the file has the correct tag
#     assert "snv-gbcf" in (tag.name for tag in gbcf.tags)
