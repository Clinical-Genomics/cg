"""Post-processing Demultiiplex API."""
import logging
import shutil
from contextlib import redirect_stdout
from pathlib import Path
from typing import Iterable, List, Optional

from cg.apps.cgstats.crud import create, find
from cg.apps.cgstats.stats import StatsAPI
from cg.apps.demultiplex.demultiplex_api import DemultiplexingAPI
from cg.apps.demultiplex.demux_report import create_demux_report
from cg.apps.housekeeper.hk import HousekeeperAPI
from cg.constants.cgstats import STATS_HEADER
from cg.constants.demultiplexing import DemultiplexingDirsAndFiles
from cg.exc import FlowcellError
from cg.meta.demultiplex import files
from cg.meta.transfer import TransferFlowcell
from cg.models.cg_config import CGConfig
from cg.models.cgstats.stats_sample import StatsSample
from cg.models.demultiplex.demux_results import DemuxResults
from cg.models.demultiplex.flowcell import FlowCell
from cg.store import Store, models
from cg.utils import Process

LOG = logging.getLogger(__name__)


class DemuxPostProcessingAPI:
    """Post demultiplexing API class."""

    def __init__(self, config: CGConfig):
        self.stats_api: StatsAPI = config.cg_stats_api
        self.demux_api: DemultiplexingAPI = config.demultiplex_api
        self.status_db: Store = config.status_db
        self.hk_api: HousekeeperAPI = config.housekeeper_api
        self.transfer_flowcell_api: TransferFlowcell = TransferFlowcell(
            db=self.status_db, stats_api=self.stats_api, hk_api=self.hk_api
        )
        self.dry_run = False

    def set_dry_run(self, dry_run: bool) -> None:
        """Set dry run."""
        LOG.debug(f"Set dry run to {dry_run}")
        self.dry_run = dry_run
        if dry_run:
            self.demux_api.set_dry_run(dry_run=dry_run)


class DemuxPostProcessingHiseqXAPI(DemuxPostProcessingAPI):
    """Post demultiplexing API class for Hiseq X flow cell."""

    def add_to_cgstats(self, flowcell_path: Path) -> None:
        """Add flow cell to cgstats."""
        LOG.info(
            f"{self.stats_api.binary} --database {self.stats_api.db_uri} add --machine X {flowcell_path.as_posix()}"
        )
        cgstats_add_parameters = [
            "--database",
            self.stats_api.db_uri,
            "add",
            "--machine",
            "X",
            flowcell_path.as_posix(),
        ]
        cgstats_process: Process = Process(binary=self.stats_api.binary)
        cgstats_process.run_command(parameters=cgstats_add_parameters, dry_run=self.dry_run)

    def cgstats_select_project(self, flowcell_id: str, flowcell_path: Path) -> None:
        """Process selected project using cgstats."""
        unaligned_dir: Path = Path(flowcell_path, DemultiplexingDirsAndFiles.UNALIGNED_DIR_NAME)
        for project_dir in unaligned_dir.glob("Project_*[0-9]*"):
            (_, project_id) = project_dir.name.split("_")
            stdout_file: Path = Path(
                flowcell_path, "-".join(["stats", project_id, flowcell_id]) + ".txt"
            )
            LOG.info(
                f"{self.stats_api.binary} --database {self.stats_api.db_uri} select --project {project_id} {flowcell_id}"
            )
            cgstats_select_parameters: List[str] = [
                "--database",
                self.stats_api.db_uri,
                "selected",
                "--project",
                project_id,
                flowcell_id,
            ]
            cgstats_process: Process = Process(binary=self.stats_api.binary)
            with open(stdout_file.as_posix(), "w") as file:
                with redirect_stdout(file):
                    cgstats_process.run_command(
                        parameters=cgstats_select_parameters, dry_run=self.dry_run
                    )

    def cgstats_lanestats(self, flowcell_path: Path) -> None:
        """Process lane stats using cgstats."""
        cgstats_lane_parameters: List[str] = [
            "--database",
            self.stats_api.db_uri,
            "lanestats",
            flowcell_path.as_posix(),
        ]
        cgstats_process: Process = Process(binary=self.stats_api.binary)
        LOG.info(
            f"{self.stats_api.binary} --database {self.stats_api.db_uri} lanestats {flowcell_path.as_posix()}"
        )
        cgstats_process.run_command(parameters=cgstats_lane_parameters, dry_run=self.dry_run)

    def post_process_flowcell(
        self, flowcell: FlowCell, flowcell_name: str, flowcell_path: Path
    ) -> None:
        """Run all the necessary steps for post-processing a demultiplexed flow cell."""
        if not flowcell.is_hiseq_x_copy_completed():
            LOG.info(f"{flowcell_name} is not yet completely copied")
            return
        if flowcell.is_hiseq_x_delivery_started():
            LOG.info(f"{flowcell_name} copy is complete and delivery has already started")
            return
        if not flowcell.is_hiseq_x():
            LOG.debug(f"{flowcell_name} is not an Hiseq X flow cell")
            return
        LOG.info(f"{flowcell_name} copy is complete and delivery will start")
        Path(flowcell_path, DemultiplexingDirsAndFiles.DELIVERY).touch()
        self.add_to_cgstats(flowcell_path=flowcell_path)
        self.cgstats_select_project(flowcell_id=flowcell.id, flowcell_path=flowcell_path)
        self.cgstats_lanestats(flowcell_path=flowcell_path)
        new_record: models.Flowcell = self.transfer_flowcell_api.transfer(flow_cell_id=flowcell.id)
        self.status_db.add_commit(new_record)
        LOG.info(f"Flow cell added: {new_record}")

    def finish_flowcell(self, bcl_converter: str, flowcell_name: str, flowcell_path: Path) -> None:
        """Post-processing flow cell."""
        LOG.info(f"Check demultiplexed flow cell {flowcell_name}")
        try:
            flowcell: FlowCell = FlowCell(flow_cell_path=flowcell_path, bcl_converter=bcl_converter)
        except FlowcellError:
            return
        self.post_process_flowcell(
            flowcell=flowcell, flowcell_name=flowcell_name, flowcell_path=flowcell_path
        )

    def finish_all_flowcells(self, bcl_converter: str) -> None:
        """Loop over all flow cells and post process those that need it."""
        demultiplex_flow_cell_out_dirs: List[
            Path
        ] = self.demux_api.get_all_demultiplex_flow_cells_out_dirs()
        for flowcell_dir in demultiplex_flow_cell_out_dirs:
            self.finish_flowcell(
                bcl_converter=bcl_converter,
                flowcell_name=flowcell_dir.name,
                flowcell_path=flowcell_dir,
            )


class DemuxPostProcessingNovaseqAPI(DemuxPostProcessingAPI):
    """Post demultiplexing API class for Novaseq flow cell."""

    def rename_files(self, demux_results: DemuxResults) -> None:
        """Rename the files according to how we want to have it after demultiplexing is ready"""
        LOG.info(f"Renaming files for flowcell {demux_results.flowcell.flow_cell_full_name}")
        flowcell_id: str = demux_results.flowcell.id
        for project_dir in demux_results.raw_projects:
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
            yield DemuxPostProcessingNovaseqAPI.sample_to_report_line(
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

        return list(self.get_report_lines(stats_samples=project_samples, flowcell_id=flowcell_id))

    def create_cgstats_reports(self, demux_results: DemuxResults) -> None:
        """Create a report for every project that was demultiplexed"""
        flowcell_id: str = demux_results.flowcell.id
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

    def post_process_flowcell(self, demux_results: DemuxResults, flowcell_id: str) -> None:
        """Run all the necessary steps for post-processing a demultiplexed flowcell

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
        if demux_results.bcl_converter == "bcl2fastq":
            self.create_barcode_summary_report(demux_results=demux_results)
        self.copy_sample_sheet(demux_results=demux_results)
        new_record: models.Flowcell = self.transfer_flowcell_api.transfer(flow_cell_id=flowcell_id)
        self.status_db.add_commit(new_record)
        LOG.info(f"Flow cell added: {new_record}")

    def finish_flowcell(self, flowcell_name: str, bcl_converter: str, force: bool = False) -> None:
        """Go through the post processing steps for a flowcell

        Force is used to finish a flowcell even if the files are renamed already
        """
        LOG.info("Check demuxed flowcell %s", flowcell_name)
        try:
            flowcell: FlowCell = FlowCell(
                flow_cell_path=self.demux_api.run_dir / flowcell_name, bcl_converter=bcl_converter
            )
        except FlowcellError:
            return
        if not self.demux_api.is_demultiplexing_completed(flowcell=flowcell):
            LOG.warning("Demultiplex is not ready for %s", flowcell_name)
            return
        demux_results: DemuxResults = DemuxResults(
            demux_dir=self.demux_api.out_dir / flowcell_name,
            flowcell=flowcell,
            bcl_converter=bcl_converter,
        )
        if not demux_results.results_dir.exists():
            LOG.warning("Could not find results directory %s", demux_results.results_dir)
            LOG.info("Can not finish flowcell %s", flowcell_name)
            return
        if demux_results.files_renamed():
            LOG.warning("Flow cell is already finished!")
            if not force:
                return
            LOG.info("Post processing flowcell anyway")
        self.post_process_flowcell(demux_results=demux_results, flowcell_id=flowcell.id)

    def finish_all_flowcells(self, bcl_converter: str) -> None:
        """Loop over all flowcells and post process those that need it"""
        demuxed_flowcells_dir: Path = self.demux_api.out_dir
        for flowcell_dir in demuxed_flowcells_dir.iterdir():
            if not flowcell_dir.is_dir():
                continue
            self.finish_flowcell(flowcell_name=flowcell_dir.name, bcl_converter=bcl_converter)
