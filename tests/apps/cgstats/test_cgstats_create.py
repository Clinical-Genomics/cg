from cg.apps.cgstats.crud import create
from cg.apps.cgstats.db.models import Supportparams, Datasource, Flowcell
from cg.apps.cgstats.stats import StatsAPI
from cg.models.demultiplex.demux_results import DemuxResults


def test_create_support_parameters(stats_api: StatsAPI, bcl2fastq_demux_results: DemuxResults):
    # GIVEN a cg stats api without any support parameter for the demux result
    document_path = str(bcl2fastq_demux_results.results_dir)
    assert not stats_api.find_handler.get_support_parameters_by_document_path(
        document_path=document_path
    )

    # WHEN creating the new support parameters
    create.create_support_parameters(manager=stats_api, demux_results=bcl2fastq_demux_results)

    # THEN assert that the parameters was created
    document_path: str = str(bcl2fastq_demux_results.results_dir)
    support_parameters = stats_api.find_handler.get_support_parameters_by_document_path(
        document_path=document_path
    )
    assert isinstance(support_parameters, Supportparams)


def test_create_data_source(stats_api: StatsAPI, bcl2fastq_demux_results: DemuxResults):
    # GIVEN a api with some support parameters
    support_parameters: Supportparams = create.create_support_parameters(
        manager=stats_api, demux_results=bcl2fastq_demux_results
    )
    document_path: str = str(bcl2fastq_demux_results.conversion_stats_path)

    # GIVEN that there are no data source for the given run
    assert not stats_api.find_handler.get_datasource_by_document_path(document_path=document_path)

    # WHEN creating a new datasource
    create.create_datasource(
        manager=stats_api,
        demux_results=bcl2fastq_demux_results,
        support_parameters_id=support_parameters.supportparams_id,
    )

    # THEN assert that the datasource exists
    assert stats_api.find_handler.get_datasource_by_document_path(document_path=document_path)


def test_create_flowcell(stats_api: StatsAPI, bcl2fastq_demux_results: DemuxResults):
    # GIVEN a api without a flowcell object
    assert not stats_api.find_handler.get_flow_cell_by_name(
        flow_cell_name=bcl2fastq_demux_results.flow_cell.id
    )

    # WHEN creating a new flowcell
    create.create_flowcell(manager=stats_api, demux_results=bcl2fastq_demux_results)

    # THEN assert that the flowcell was created
    assert stats_api.find_handler.get_flow_cell_by_name(
        flow_cell_name=bcl2fastq_demux_results.flow_cell.id
    )


def test_create_demux(stats_api: StatsAPI, bcl2fastq_demux_results: DemuxResults):
    # GIVEN a database with a flowcell and a data source
    support_parameters: Supportparams = create.create_support_parameters(
        manager=stats_api, demux_results=bcl2fastq_demux_results
    )
    flowcell: Flowcell = create.create_flowcell(
        manager=stats_api, demux_results=bcl2fastq_demux_results
    )
    data_source: Datasource = create.create_datasource(
        manager=stats_api,
        demux_results=bcl2fastq_demux_results,
        support_parameters_id=support_parameters.supportparams_id,
    )
    # GIVEN that there is not demux object in the database
    assert not stats_api.find_handler.get_demux_by_flow_cell_id_and_base_mask(
        flowcell_id=flowcell.flowcell_id
    )

    # WHEN creating a demux object
    create.create_demux(
        manager=stats_api,
        demux_results=bcl2fastq_demux_results,
        flow_cell_id=flowcell.flowcell_id,
        datasource_id=data_source.datasource_id,
    )

    # THEN assert that a demux object was created
    assert stats_api.find_handler.get_demux_by_flow_cell_id_and_base_mask(
        flowcell_id=flowcell.flowcell_id
    )


def test_create_dragen_demux(stats_api: StatsAPI, dragen_demux_results: DemuxResults):
    # GIVEN a database with a flowcell and a data source
    support_parameters: Supportparams = create.create_support_parameters(
        manager=stats_api, demux_results=dragen_demux_results
    )
    flowcell: Flowcell = create.create_flowcell(
        manager=stats_api, demux_results=dragen_demux_results
    )
    data_source: Datasource = create.create_datasource(
        manager=stats_api,
        demux_results=dragen_demux_results,
        support_parameters_id=support_parameters.supportparams_id,
    )
    # GIVEN that there is not demux object in the database
    assert not stats_api.find_handler.get_demux_by_flow_cell_id_and_base_mask(
        flowcell_id=flowcell.flowcell_id
    )

    # WHEN creating a demux object
    demux_object = create.create_demux(
        manager=stats_api,
        demux_results=dragen_demux_results,
        flow_cell_id=flowcell.flowcell_id,
        datasource_id=data_source.datasource_id,
    )

    # THEN assert that a demux object was created
    assert stats_api.find_handler.get_demux_by_flow_cell_id_and_base_mask(
        flowcell_id=flowcell.flowcell_id, base_mask=demux_object.basemask
    )
