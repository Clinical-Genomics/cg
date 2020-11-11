from cg.store import Store
from cg.meta.workflow.mip import MipAnalysisAPI
import logging


def test_config(analysis_store: Store, analysis_api: MipAnalysisAPI):

    # GIVEN a status db with a family
    family_obj = analysis_store.families().first()
    assert family_obj is not None
    for link_obj in family_obj.links:
        link_obj.sample.application_version.application.min_sequencing_depth = 10
        analysis_store.commit()

    # WHEN generating the MIP config for the family
    mip_config = analysis_api.pedigree_config(family_obj, pipeline="mip-dna")

    # THEN it should fill in values accordingly
    assert len(mip_config["samples"]) == len(family_obj.links)


def test_get_latest_data_genome_build(analysis_api: MipAnalysisAPI, case_id: str):

    # GIVEN

    # WHEN
    trending_data = analysis_api.get_latest_metadata(case_id)

    # THEN contains genome_build
    assert trending_data["genome_build"]


def test_get_latest_data_rank_model_version(analysis_api: MipAnalysisAPI, case_id: str):
    # GIVEN

    # WHEN
    trending_data = analysis_api.get_latest_metadata(case_id)

    # THEN contains rankmodelversion
    assert trending_data["rank_model_version"]


def test_get_latest_metadata_logging(caplog, analysis_api: MipAnalysisAPI):
    # GIVEN an initialised report_api and the deliver_api does not have what we want
    family_id = "case_missing_data"
    # WHEN failing to get latest trending data for a family
    latest_data = analysis_api.get_latest_metadata(family_id)

    with caplog.at_level(logging.WARNING):
        assert family_id in caplog.text
    # THEN there should be a log entry about this
    assert not latest_data
