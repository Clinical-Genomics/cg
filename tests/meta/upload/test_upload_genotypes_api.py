"""Tests for the upload genotypes api"""

from datetime import datetime
from pathlib import Path

from cg.meta.upload.gt import UploadGenotypesAPI
from cg.models.mip.mip_metrics_deliverables import MetricsDeliverables
from cg.store import models


def test_get_analysis_sex(case_qc_metrics_deliverables: Path, genotype_analysis_sex: dict):
    """Test to get the predicted sex from a MIP run using the upload genotypes API"""
    # GIVEN a UploadGenotypesAPI some qcmetrics data

    # WHEN fetching the predicted sex by the analysis
    sex: dict = UploadGenotypesAPI.analysis_sex(
        self=UploadGenotypesAPI, qc_metrics_file=case_qc_metrics_deliverables
    )

    # THEN assert that the the predicted sex per sample_id is returned
    assert sex == genotype_analysis_sex


def test_get_parsed_qc_metrics_data(case_qc_metrics_deliverables: Path):
    """Test to get the predicted sex from a MIP run using the upload genotypes API"""
    # GIVEN a UploadGenotypesAPI and the path to a qc_metrics file with case data

    # WHEN fetching the predicted sex
    metrics_object: MetricsDeliverables = UploadGenotypesAPI.get_parsed_qc_metrics_data(
        case_qc_metrics_deliverables
    )

    # THEN assert that it was successfully created
    assert isinstance(metrics_object, MetricsDeliverables)


def test_get_bcf_file(upload_genotypes_api: UploadGenotypesAPI, case_id: str, timestamp: datetime):
    """Test to get the predicted sex from a MIP run using the upload genotypes API"""
    # GIVEN a UploadGenotypesAPI populated with some data in housekeeper
    hk_version = upload_genotypes_api.hk.version(case_id, timestamp)

    # WHEN fetching the gbcf file with the api
    gbcf = upload_genotypes_api.get_bcf_file(hk_version)

    # THEN assert that the file has the correct tag
    assert "snv-gbcf" in (tag.name for tag in gbcf.tags)


def test_get_data(
    analysis_obj: models.Analysis,
    genotype_analysis_sex: dict,
    mocker,
    upload_genotypes_api: UploadGenotypesAPI,
):
    """Test to get data from the UploadGenotypesAPI"""
    # GIVEN a UploadGenotypeAPI populated with some data
    # GIVEN an analysis object with a trio

    # GIVEN analysis sex were generated and could be found
    mocker.patch.object(UploadGenotypesAPI, "analysis_sex")
    UploadGenotypesAPI.analysis_sex.return_value = genotype_analysis_sex

    # WHEN parsing the data
    result = upload_genotypes_api.data(analysis_obj=analysis_obj)

    # THEN assert that the result looks like expected
    assert len(result["samples_sex"]) == 3
