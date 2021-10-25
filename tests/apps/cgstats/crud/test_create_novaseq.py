from cg.apps.cgstats.crud import create, find
from cg.apps.cgstats.stats import StatsAPI
from cg.models.demultiplex.demux_results import DemuxResults


def test_create_novaseq_flowcell(stats_api: StatsAPI, bcl2fastq_demux_results: DemuxResults):
    # GIVEN a setup with an existing sample sheet with information
    assert bcl2fastq_demux_results.flowcell.sample_sheet_path.read_text()
    # GIVEN that the flowcell does not exist in the database
    assert not find.get_flowcell_id(flowcell_name=bcl2fastq_demux_results.flowcell.flowcell_id)

    # WHEN creating the novaseq flowcell
    create.create_novaseq_flowcell(manager=stats_api, demux_results=bcl2fastq_demux_results)

    # THEN assert that the flowcell was created
    assert find.get_flowcell_id(flowcell_name=bcl2fastq_demux_results.flowcell.flowcell_id)
