from cg.apps.cgstats import create, find
from cg.apps.cgstats.stats import StatsAPI
from cg.models.demultiplex.demux_results import DemuxResults


def test_hej():
    assert "hej"


# def test_create_support_parameters(stats_api: StatsAPI, demux_results: DemuxResults):
#     # GIVEN a cg stats api without any support parameter for the demux result
#     assert not find.get_support_parameters_id(manager=stats_api, demux_results=demux_results)
#
#     # WHEN creating the new support parameters
#     assert 0
