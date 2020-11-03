"""Tests for the upload genotypes api"""

from datetime import datetime
from pathlib import Path

from cg.meta.upload.gt import UploadGenotypesAPI
from cg.store import models
import ruamel.yaml
from cg.apps.mip import parse_qcmetrics


def test_get_sample_sex():
    """Test to get the predicted sex from a MIP run using the upload genotypes API"""
    # GIVEN a UploadGenotypesAPI some qcmetrics data
    qcmetrics_file_path = "tests/fixtures/apps/mip/case_qc_metrics.yaml"
    qcmetrics_dict = ruamel.yaml.safe_load(open(qcmetrics_file_path))
    qcmetrics_parsed = parse_qcmetrics.parse_qcmetrics(qcmetrics_dict)

    # WHEN fetching the predicted "gender" for the individual with id "father"
    sex = UploadGenotypesAPI.get_sample_predicted_sex(
        sample_id="ADM2", parsed_qcmetrics_data=qcmetrics_parsed
    )

    # THEN assert that the "gender" was "male"
    assert sex == "male"


def test_get_parsed_qc_metrics_data(case_qc_metrics: Path):
    """Test to get the predicted sex from a MIP run using the upload genotypes API"""
    # GIVEN a UploadGenotypesAPI and the path to a qcmetrics file with case data

    # WHEN fetching the predicted gender for the individual with id "father"

    qcmetrics_parsed = UploadGenotypesAPI.get_parsed_qc_metrics_data(case_qc_metrics)

    # THEN assert that there are three samples in the case qc metrics file
    assert len(qcmetrics_parsed) == 3


def test_get_bcf_file(upload_genotypes_api: UploadGenotypesAPI, case_id: str, timestamp: datetime):
    """Test to get the predicted sex from a MIP run using the upload genotypes API"""
    # GIVEN a UploadGenotypesAPI populated with some data in housekeeper
    hk_version = upload_genotypes_api.hk.version(case_id, timestamp)

    # WHEN fetching the gbcf file with the api
    gbcf = upload_genotypes_api.get_bcf_file(hk_version)

    # THEN assert that the file has the correct tag
    assert "snv-gbcf" in (tag.name for tag in gbcf.tags)


def test_get_data(upload_genotypes_api: UploadGenotypesAPI, analysis_obj: models.Analysis):
    """Test to get data from the UploadGenotypesAPI"""
    # GIVEN a UploadGenotypeAPI populated with some data
    # GIVEN an analysis object with a trio

    # WHEN parsing the data
    result = upload_genotypes_api.data(analysis_obj=analysis_obj)

    # THEN assert that the result looks like expected
    assert len(result["samples_sex"]) == 3
