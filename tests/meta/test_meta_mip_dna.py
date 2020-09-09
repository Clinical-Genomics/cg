from cg.store import Store
from cg.meta.workflow.mip import AnalysisAPI


def test_config(analysis_store: Store, analysis_api: AnalysisAPI):

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


def test_get_latest_data_genome_build(analysis_api: AnalysisAPI):

    # GIVEN
    family_id = "dummy_family_id"

    # WHEN
    trending_data = analysis_api.get_latest_metadata(family_id)

    # THEN contains genome_build
    assert trending_data["genome_build"]


def test_get_latest_data_rank_model_version(analysis_api: AnalysisAPI):
    # GIVEN
    family_id = "dummy_family_id"

    # WHEN
    trending_data = analysis_api.get_latest_metadata(family_id)

    # THEN contains rankmodelversion
    assert trending_data["rank_model_version"]


def test_get_latest_metadata_logging(analysis_api: AnalysisAPI):
    # GIVEN an initialised report_api and the deliver_api does not have what we want
    analysis_api.tb._get_trending_raises_keyerror = True

    # WHEN failing to get latest trending data for a family
    latest_data = analysis_api.get_latest_metadata(family_id="bluebull")

    # THEN there should be a log entry about this
    found = False
    for warn in analysis_api.log.get_warnings():
        if "bluebull" in warn:
            found = True

    assert found
    assert not latest_data
