import logging
import shutil
from pathlib import Path
from typing import Iterable, List, Optional

from cg.apps.cgstats.crud import create, find
from cg.apps.cgstats.stats import StatsAPI
from cg.apps.demultiplex.demultiplex_api import DemultiplexingAPI
from cg.apps.demultiplex.demux_report import create_demux_report
from cg.constants.cgstats import STATS_HEADER
from cg.exc import FlowcellError
from cg.meta.demultiplex import files
from cg.models.cg_config import CGConfig
from cg.models.cgstats.stats_sample import StatsSample
from cg.models.demultiplex.demux_results import DemuxResults
from cg.models.demultiplex.flowcell import Flowcell

LOG = logging.getLogger(__name__)


class DemuxPostProcessingAPI:
    def __init__(self, config: CGConfig):
        self.stats_api: StatsAPI = config.cg_stats_api
        self.demux_api: DemultiplexingAPI = config.demultiplex_api
        self.dry_run = False

    def set_dry_run(self, dry_run: bool) -> None:
        LOG.debug("Set dry run to %s", dry_run)
        self.dry_run = dry_run
        if dry_run:
            self.demux_api.set_dry_run(dry_run=dry_run)

    def rename_files(self, demux_results: DemuxResults) -> None:
        """Rename the files according to how we want to have it after demultiplexing is ready"""
        LOG.info("Renaming files for flowcell %s", demux_results.flowcell.flowcell_full_name)
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
    def fetch_report_samples(flowcell_id: str, project_name: str) -> List[StatsSample]:
        samples: List[StatsSample] = find.project_sample_stats(
            flowcell=flowcell_id, project_name=project_name
        )
        LOG.info(
            "Found samples: %s for flowcell: %s, project: %s",
            ",".join(sample.sample_name for sample in samples),
            flowcell_id,
            project_name,
        )
        return samples

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
    def write_report(report_path: Path, report_data: List[str]) -> None:
        LOG.info("Write demux report to %s", report_path)
        with report_path.open("w") as report_file:
            report_file.write("\t".join(STATS_HEADER) + "\n")
            for line in report_data:
                report_file.write(line + "\n")

    def get_report_data(self, flowcell_id: str, project_name: Optional[str] = None) -> List[str]:
        """Fetch the lines that are used to make a report from a flowcell"""
        LOG.info("Fetch report data for flowcell: %s project: %s", flowcell_id, project_name)
        project_samples: List[StatsSample] = self.fetch_report_samples(
            flowcell_id=flowcell_id, project_name=project_name
        )

        return [
            sample_line
            for sample_line in self.get_report_lines(
                stats_samples=project_samples, flowcell_id=flowcell_id
            )
        ]

    def create_cgstats_reports(self, demux_results: DemuxResults) -> None:
        """Create a report for every project that was demultiplexed"""
        flowcell_id: str = demux_results.flowcell.flowcell_id
        for project in demux_results.projects:
            project_name: str = project.split("_")[-1]
            report_data: List[str] = self.get_report_data(
                flowcell_id=flowcell_id, project_name=project_name
            )
            report_path: Path = demux_results.demux_dir / f"stats-{project_name}-{flowcell_id}.txt"
            self.write_report(report_path=report_path, report_data=report_data)

    @staticmethod
    def create_barcode_summary_report(demux_results: DemuxResults) -> None:
        report_content = create_demux_report(conversion_stats=demux_results.conversion_stats)
        report_path: Path = demux_results.barcode_report
        if report_path.exists():
            LOG.warning("Report path already exists!")
            return
        LOG.info("Write demux report to %s", report_path)
        with report_path.open("w") as report_file:
            report_file.write("\n".join(report_content))

    @staticmethod
    def copy_sample_sheet(demux_results: DemuxResults) -> None:
        """Copy the sample sheet from run dir to demux dir"""
        LOG.info(
            "Copy sample sheet (%s) from flowcell to demuxed result dir (%s)",
            demux_results.sample_sheet_path,
            demux_results.demux_sample_sheet_path,
        )
        shutil.copy(
            demux_results.sample_sheet_path.as_posix(),
            demux_results.demux_sample_sheet_path.as_posix(),
        )

    @staticmethod
    def create_copy_complete_file(demux_results: DemuxResults) -> None:
        """Suggestion is to deprecate this as a flag and store information in database instead"""
        LOG.info("Creating %s", demux_results.copy_complete_path)
        demux_results.copy_complete_path.touch()

    def post_process_flowcell(self, demux_results: DemuxResults) -> None:
        """Run all the necessary steps for post processing a demultiplexed flowcell

        This will
            1. rename all the necessary files and folders
            2. add the demux results to cgstats
            3. produce reports for every project
            4. generate a report with samples that have low cluster count
        """
        if demux_results.files_renamed():
            LOG.info("Files have already been renamed")
        else:
            self.rename_files(demux_results=demux_results)
        self.add_to_cgstats(demux_results=demux_results)
        self.create_cgstats_reports(demux_results=demux_results)
        self.create_barcode_summary_report(demux_results=demux_results)
        self.copy_sample_sheet(demux_results=demux_results)
        self.create_copy_complete_file(demux_results=demux_results)

    def finish_flowcell(self, flowcell_name: str, force: bool = False) -> None:
        """Go through the post processing steps for a flowcell

        Force is used to finish a flowcell even if the files are renamed already
        """
        LOG.info("Check demuxed flowcell %s", flowcell_name)
        try:
            flowcell: Flowcell = Flowcell(flowcell_path=self.demux_api.run_dir / flowcell_name)
        except FlowcellError:
            return
        if not self.demux_api.is_demultiplexing_completed(flowcell=flowcell):
            LOG.warning("Demultiplex is not ready for %s", flowcell_name)
            return
        demux_results: DemuxResults = DemuxResults(
            demux_dir=self.demux_api.out_dir / flowcell_name, flowcell=flowcell
        )
        if not demux_results.results_dir.exists():
            LOG.warning("Could not find results directory %s", demux_results.results_dir)
            LOG.info("Can not finish flowcell %s", flowcell_name)
            return
        if demux_results.files_renamed():
            LOG.warning("Flowcell is already finished!")
            if not force:
                return
            LOG.info("Post processing flowcell anyway")
        self.post_process_flowcell(demux_results=demux_results)

    def finish_all_flowcells(self) -> None:
        """Loop over all flowcells and post process those that need it"""
        demuxed_flowcells_dir: Path = self.demux_api.out_dir
        for flowcell_dir in demuxed_flowcells_dir.iterdir():
            if not flowcell_dir.is_dir():
                continue
            self.finish_flowcell(flowcell_name=flowcell_dir.name)
