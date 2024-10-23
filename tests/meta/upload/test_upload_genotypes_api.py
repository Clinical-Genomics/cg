"""Tests for the upload Genotypes API."""

from pathlib import Path

from cg.constants import Workflow
from cg.constants.constants import SexOptions
from cg.constants.observations import MipDNAObservationsAnalysisTag
from cg.meta.upload.gt import UploadGenotypesAPI
from cg.models.deliverables.metric_deliverables import MetricsBase
from cg.models.mip.mip_metrics_deliverables import MIPMetricsDeliverables
from cg.store.models import Analysis


def test_get_analysis_sex(case_qc_metrics_deliverables: Path, genotype_analysis_sex: dict):
    """Test to get the predicted sex from a MIP run using the upload genotypes API"""
    # GIVEN a UploadGenotypesAPI some qcmetrics data

    # WHEN fetching the predicted sex by the analysis
    sex: dict = UploadGenotypesAPI._get_analysis_sex_mip_dna(
        qc_metrics_file=case_qc_metrics_deliverables
    )

    # THEN assert that the the predicted sex per sample_id is returned
    assert sex == genotype_analysis_sex


def test_get_analysis_sex_raredisease(
    case_qc_metrics_deliverables_raredisease: Path, sample_id: str
):
    """Test to get the predicted sex from a MIP run using the upload Genotypes API"""
    # GIVEN a UploadGenotypesAPI some qcmetrics data

    # WHEN fetching the predicted sex by the analysis
    sex: str = UploadGenotypesAPI._get_analysis_sex_raredisease(
        UploadGenotypesAPI,
        qc_metrics_file=case_qc_metrics_deliverables_raredisease,
        sample_id=sample_id,
    )

    # THEN assert that the the predicted sex per sample_id is returned
    assert sex == SexOptions.MALE


def test_get_parsed_qc_metrics_deliverables_mip(case_qc_metrics_deliverables: Path):
    """Test to get the predicted sex from a MIP run using the upload genotypes API"""
    # GIVEN a UploadGenotypesAPI and the path to a qc_metrics file with case data

    # WHEN fetching the predicted sex
    metrics_object: MIPMetricsDeliverables = (
        UploadGenotypesAPI._get_parsed_qc_metrics_deliverables_mip_dna(case_qc_metrics_deliverables)
    )
    # THEN assert that it was successfully created
    assert isinstance(metrics_object, MIPMetricsDeliverables)


def test_get_parsed_qc_metrics_deliverables_raredisease(case_qc_metrics_deliverables: Path):
    """Test to get the predicted sex from a MIP run using the upload genotypes API"""
    # GIVEN a UploadGenotypesAPI and the path to a QC metrics file with case data

    # WHEN fetching the predicted sex
    metrics_object = UploadGenotypesAPI._get_parsed_qc_metrics_deliverables_raredisease(
        case_qc_metrics_deliverables
    )

    # First, check if the object is a list
    assert isinstance(metrics_object, list)

    # Then, check if all items in the list are instances of MetricsBase
    assert all(isinstance(item, MetricsBase) for item in metrics_object)


def test_get_genotype_file(upload_genotypes_api: UploadGenotypesAPI, case_id: str):
    """Test to get the predicted sex from a MIP run using the upload genotypes API"""
    # GIVEN a UploadGenotypesAPI populated with some data in housekeeper

    # WHEN fetching the gbcf file with the api
    gbcf = upload_genotypes_api._get_genotype_file(case_id)

    # THEN assert that the file has the correct tag
    assert MipDNAObservationsAnalysisTag.PROFILE_GBCF in (tag.name for tag in gbcf.tags)


def test_get_data_mip(
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

    analysis_obj.workflow = Workflow.MIP_DNA

    # WHEN parsing the data
    result = upload_genotypes_api.get_genotype_data(analysis=analysis_obj)

    # THEN assert that the the number of samples sex is set
    assert len(result["samples_sex"]) == 3


def test_get_data_raredisease(
    analysis_obj: Analysis,
    genotype_analysis_sex: dict,
    mocker,
    upload_genotypes_api: UploadGenotypesAPI,
):
    """Test to get data from the UploadGenotypesAPI"""
    # GIVEN a UploadGenotypeAPI populated with some data
    # GIVEN an analysis object with a trio

    # GIVEN analysis sex were generated and could be found
    mocker.patch.object(UploadGenotypesAPI, "_get_analysis_sex_raredisease")
    UploadGenotypesAPI._get_analysis_sex_raredisease.return_value = genotype_analysis_sex

    analysis_obj.workflow = Workflow.RAREDISEASE

    # WHEN parsing the data
    result = upload_genotypes_api.get_genotype_data(analysis=analysis_obj)

    # THEN assert that the the number of samples sex is set
    assert len(result["samples_sex"]) == 3
