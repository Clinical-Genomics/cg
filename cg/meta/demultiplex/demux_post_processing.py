import logging
from pathlib import Path
from typing import List, Iterable

import alchy
from cg.apps.cgstats.crud import create, find
from cg.apps.cgstats.stats import StatsAPI
from cg.constants.cgstats import STATS_HEADER
from cg.meta.demultiplex import files
from cg.models.cgstats.stats_sample import StatsSample
from cg.models.demultiplex.demux_results import DemuxResults

LOG = logging.getLogger(__name__)


class DemuxPostProcessingAPI:
    def __init__(self, stats_api: StatsAPI):
        self.stats_api: StatsAPI = stats_api
        self.dry_run = False

    def set_dry_run(self, dry_run: bool) -> None:
        LOG.debug("Set dry run to %s", dry_run)
        self.dry_run = dry_run

    def rename_files(self, demux_results: DemuxResults) -> None:
        """Rename the files according to how we want to have it after demultiplexing is ready"""
        flowcell_id: str = demux_results.flowcell.flowcell_id
        for project_dir in demux_results.raw_projects:
            if "index" in project_dir.name:
                continue
            files.rename_project_directory(
                project_directory=project_dir, flowcell_id=flowcell_id, dry_run=self.dry_run
            )

    def add_to_cgstats(self, demux_results: DemuxResults) -> None:
        """Add the information from demultiplexing to cgstats"""
        create.create_novaseq_flowcell(manager=self.stats_api, demux_results=demux_results)

    @staticmethod
    def fetch_report_data(flowcell_id: str, project_name: str) -> List[StatsSample]:
        return find.project_sample_stats(flowcell=flowcell_id, project_name=project_name)

    @staticmethod
    def sample_to_report_line(stats_sample: StatsSample, flowcell_id: str) -> str:
        lanes: str = ",".join(str(lane) for lane in stats_sample.lanes)
        return "\t".join(
            [
                stats_sample.sample_name,
                flowcell_id,
                lanes,
                ",".join(str(unaligned.read_count) for unaligned in stats_sample.unaligned),
                str(stats_sample.read_count_sum),
                ",".join(str(unaligned.yield_mb) for unaligned in stats_sample.unaligned),
                str(stats_sample.sum_yield),
                ",".join(str(unaligned.q30_bases_pct) for unaligned in stats_sample.unaligned),
                ",".join(str(unaligned.mean_quality_score) for unaligned in stats_sample.unaligned),
            ]
        )

    @staticmethod
    def get_report_lines(stats_samples: List[StatsSample], flowcell_id: str) -> Iterable[str]:
        """Convert stats samples to format lines ready to print"""
        for stats_sample in sorted(stats_samples, key=lambda x: x.sample_name):
            yield DemuxPostProcessingAPI.sample_to_report_line(
                stats_sample=stats_sample, flowcell_id=flowcell_id
            )

    @staticmethod
    def write_report(report_path: Path, report_content: alchy.Query):
        LOG.info("Write demux report to %s", report_path)
        with report_path.open("w") as report_file:
            report_file.write("\t".join(STATS_HEADER) + "\n")
            for line in report_content:
                report_file.write(
                    "\t".join(
                        str(s)
                        for s in [
                            line.samplename,
                            line.flowcellname,
                            line.lanes,
                            line.reads,
                            line.readsum,
                            line.yld,
                            line.yieldsum,
                            line.q30,
                            line.meanq,
                        ]
                    )
                    + "\n"
                )

    def get_report_data(self, demux_results: DemuxResults) -> Iterable[str]:

    def create_cgstats_reports(self, demux_results: DemuxResults) -> None:
        """Create a report for every project that was demultiplexed"""
        flowcell_id: str = demux_results.flowcell.flowcell_id
        for project in demux_results.projects:
            project_name: str = project.split("_")[-1]
            report_data: alchy.Query = self.fetch_report_data(
                flowcell_id=flowcell_id, project_name=project_name
            )
            report_path: Path = demux_results.demux_dir / f"stats-{project_name}-{flowcell_id}.txt"
            self.write_report(report_path=report_path, report_content=report_data)
