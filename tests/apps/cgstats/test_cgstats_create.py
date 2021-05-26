from cg.apps.cgstats.crud import create, find
from cg.apps.cgstats.stats import StatsAPI
from cg.models.demultiplex.demux_results import DemuxResults

from cg.apps.cgstats.db import models as stats_models


def test_create_support_parameters(stats_api: StatsAPI, demux_results: DemuxResults):
    # GIVEN a cg stats api without any support parameter for the demux result
    assert not find.get_support_parameters_id(demux_results=demux_results)

    # WHEN creating the new support parameters
    create.create_support_parameters(manager=stats_api, demux_results=demux_results)

    # THEN assert that the parameters was created
    support_parameters_id = find.get_support_parameters_id(demux_results=demux_results)
    assert isinstance(support_parameters_id, int)


def test_create_data_source(stats_api: StatsAPI, demux_results: DemuxResults):
    # GIVEN a api with some support parameters
    support_parameters: stats_models.Supportparams = create.create_support_parameters(
        manager=stats_api, demux_results=demux_results
    )
    # GIVEN that there are no data source for the given run
    assert not find.get_datasource_id(demux_results=demux_results)

    # WHEN creating a new datasource
    create.create_datasource(
        manager=stats_api,
        demux_results=demux_results,
        support_parameters_id=support_parameters.supportparams_id,
    )

    # THEN assert that the datasource exists
    assert find.get_datasource_id(demux_results=demux_results)


def test_create_flowcell(stats_api: StatsAPI, demux_results: DemuxResults):
    # GIVEN a api without a flowcell object
    assert not find.get_flowcell_id(flowcell_name=demux_results.flowcell.flowcell_id)

    # WHEN creating a new flowcell
    create.create_flowcell(manager=stats_api, demux_results=demux_results)

    # THEN assert that the flowcell was created
    assert find.get_flowcell_id(flowcell_name=demux_results.flowcell.flowcell_id)


def test_create_demux(stats_api: StatsAPI, demux_results: DemuxResults):
    # GIVEN a database with a flowcell and a data source
    support_parameters: stats_models.Supportparams = create.create_support_parameters(
        manager=stats_api, demux_results=demux_results
    )
    flowcell: stats_models.Flowcell = create.create_flowcell(
        manager=stats_api, demux_results=demux_results
    )
    data_source: stats_models.Datasource = create.create_datasource(
        manager=stats_api,
        demux_results=demux_results,
        support_parameters_id=support_parameters.supportparams_id,
    )
    # GIVEN that there is not demux object in the database
    assert not find.get_demux_id(flowcell_object_id=flowcell.flowcell_id)

    # WHEN creating a demux object
    create.create_demux(
        manager=stats_api, flowcell_id=flowcell.flowcell_id, datasource_id=data_source.datasource_id
    )

    # THEN assert that a demux object was created
    assert find.get_demux_id(flowcell_object_id=flowcell.flowcell_id)
