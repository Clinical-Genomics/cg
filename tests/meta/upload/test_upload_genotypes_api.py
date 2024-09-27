"""Tests for the upload genotypes api"""

from datetime import datetime
from pathlib import Path

from cg.apps.gt import GenotypeAPI
from cg.meta.upload.gt import UploadGenotypesAPI
from cg.models.mip.mip_metrics_deliverables import MIPMetricsDeliverables
from cg.store.models import Analysis
from tests.mocks.hk_mock import MockHousekeeperAPI


def test_get_analysis_sex(case_qc_metrics_deliverables: Path, genotype_analysis_sex: dict):
    """Test to get the predicted sex from a MIP run using the upload genotypes API"""
    # GIVEN a UploadGenotypesAPI some qcmetrics data
    # hk_api =  MockHousekeeperAPI()
    # gt_api = GenotypeAPI(config={})
    # upload_genotypes_api = UploadGenotypesAPI(hk_api, gt_api )

    # WHEN fetching the predicted sex by the analysis
    sex: dict = UploadGenotypesAPI._get_analysis_sex_mip_dna(
        qc_metrics_file=case_qc_metrics_deliverables
    )

    # THEN assert that the the predicted sex per sample_id is returned
    assert sex == genotype_analysis_sex


def test_get_parsed_qc_metrics_data(case_qc_metrics_deliverables: Path):
    """Test to get the predicted sex from a MIP run using the upload genotypes API"""
    # GIVEN a UploadGenotypesAPI and the path to a qc_metrics file with case data

    # WHEN fetching the predicted sex
    metrics_object: MIPMetricsDeliverables = UploadGenotypesAPI._get_parsed_qc_metrics_data_mip_dna(
        case_qc_metrics_deliverables
    )

    # THEN assert that it was successfully created
    assert isinstance(metrics_object, MIPMetricsDeliverables)


def test_get_bcf_file(upload_genotypes_api: UploadGenotypesAPI, case_id: str, timestamp: datetime):
    """Test to get the predicted sex from a MIP run using the upload genotypes API"""
    # GIVEN a UploadGenotypesAPI populated with some data in housekeeper
    # hk_version = upload_genotypes_api.hk.version(case_id, timestamp)

    # WHEN fetching the gbcf file with the api
    gbcf = upload_genotypes_api._get_bcf_file(case_id)

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
    # GIVEN an analysis object with a trio

    # GIVEN analysis sex were generated and could be found
    mocker.patch.object(UploadGenotypesAPI, "_get_analysis_sex_mip_dna")
    UploadGenotypesAPI._get_analysis_sex_mip_dna.return_value = genotype_analysis_sex

    # WHEN parsing the data
    result = upload_genotypes_api.get_genotype_data(analysis=analysis_obj)

    # THEN assert that the result looks like expected
    assert len(result["samples_sex"]) == 3
