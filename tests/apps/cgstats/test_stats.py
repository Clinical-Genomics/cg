from typing import Dict, Union

from cg.apps.cgstats.db import models as stats_model
from cg.apps.cgstats.stats import StatsAPI


def test_flow_cell_reads_and_q30_summary(
    nipt_stats_api: StatsAPI, flow_cell_id: str, sample_id: str
):
    # GIVEN a flow cell with only one sample on it with 90% Q30 and 1200000000 yield
    sample_obj: stats_model.Sample = nipt_stats_api.Sample.query.filter(
        stats_model.Sample.limsid == sample_id
    ).first()
    unaligned_obj: stats_model.Unaligned = (
        nipt_stats_api.Unaligned.query.join(stats_model.Flowcell.demux, stats_model.Demux.unaligned)
        .filter(stats_model.Unaligned.sample_id == sample_obj.sample_id)
        .first()
    )
    # WHEN retrieving reads and q30 summary from flow cell on which the sample ran
    flow_cell_reads_and_q30_summary: Dict[
        str, Union[int, float]
    ] = nipt_stats_api.flow_cell_reads_and_q30_summary(flow_cell_name=flow_cell_id)
    # THEN the number of reads on the flow cell
    assert flow_cell_reads_and_q30_summary["reads"] == unaligned_obj.readcounts
    # AND the percent of clusters passed q30 is equel to the one sample
    assert flow_cell_reads_and_q30_summary["q30"] == float(unaligned_obj.q30_bases_pct)
