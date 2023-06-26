"""Post-processing Demultiiplex API."""
import logging
import re
import shutil
from contextlib import redirect_stdout
from pathlib import Path
from typing import Iterable, List, Optional

from housekeeper.store.models import Version

from cg.apps.cgstats.crud import create
from cg.apps.cgstats.stats import StatsAPI
from cg.apps.demultiplex.demultiplex_api import DemultiplexingAPI
from cg.apps.demultiplex.demux_report import create_demux_report
from cg.apps.demultiplex.sample_sheet.models import FlowCellSample
from cg.apps.housekeeper.hk import HousekeeperAPI
from cg.apps.sequencing_metrics_parser.api import (
    create_sample_lane_sequencing_metrics_for_flow_cell,
)
from cg.constants.cgstats import STATS_HEADER
from cg.constants.constants import FileExtensions
from cg.constants.demultiplexing import BclConverter, DemultiplexingDirsAndFiles
from cg.constants.housekeeper_tags import SequencingFileTag
from cg.exc import FlowCellError
from cg.meta.demultiplex import files
from cg.meta.transfer import TransferFlowCell
from cg.models.cg_config import CGConfig
from cg.models.cgstats.stats_sample import StatsSample
from cg.models.demultiplex.demux_results import DemuxResults
from cg.models.demultiplex.flow_cell import FlowCellDirectoryData
from cg.store import Store
from cg.store.models import Flowcell, SampleLaneSequencingMetrics
from cg.utils import Process

LOG = logging.getLogger(__name__)


class DemuxPostProcessingAPI:
    """Post demultiplexing API class."""

    def __init__(self, config: CGConfig) -> None:
        self.stats_api: StatsAPI = config.cg_stats_api
        self.demux_api: DemultiplexingAPI = config.demultiplex_api
        self.status_db: Store = config.status_db
        self.hk_api: HousekeeperAPI = config.housekeeper_api
        self.transfer_flow_cell_api: TransferFlowCell = TransferFlowCell(
            db=self.status_db, stats_api=self.stats_api, hk_api=self.hk_api
        )
        self.dry_run = False

    def set_dry_run(self, dry_run: bool) -> None:
        """Set dry run."""
        LOG.debug(f"Set dry run to {dry_run}")
        self.dry_run = dry_run
        if dry_run:
            self.demux_api.set_dry_run(dry_run=dry_run)

    def transfer_flow_cell(
        self, flow_cell_dir: Path, flow_cell_id: str, store: bool = True
    ) -> None:
        """Transfer flow cell and sequencing files."""
        flow_cell: Flowcell = self.transfer_flow_cell_api.transfer(
            flow_cell_dir=flow_cell_dir, flow_cell_id=flow_cell_id, store=store
        )
        if self.dry_run:
            LOG.info("Dry run will not commit flow cell to database")
            return
        self.status_db.session.add(flow_cell)
        self.status_db.session.commit()

        LOG.info(f"Flow cell added: {flow_cell}")

    def finish_flow_cell_temp(self, flow_cell_directory_name: str) -> None:
        """Finalize the flow cell once the temporary demultiplexing process is completed.

        This function:
            - Parses and validates the flow cell directory data
            - Stores the flow cell in the status database
            - Stores sequencing metrics in the status database
            - Updates sample read counts in the status database
            - Stores the flow cell data in the housekeeper database

        Args:
            flow_cell_directory_name (str): The name of the flow cell directory to be finalized.

        Raises:
            FlowCellError: If the flow cell directory or the data it contains is not valid.

        Note:
            This method does not return anything but updates the status and housekeeper databases
            with data from the flow cell directory.
        """

        LOG.info(f"Finish flow cell {flow_cell_directory_name}")

        flow_cell_directory_path: Path = Path(self.demux_api.out_dir, flow_cell_directory_name)
        bcl_converter: str = self.get_bcl_converter_name(
            flow_cell_directory=flow_cell_directory_path
        )

        parsed_flow_cell: FlowCellDirectoryData = self.parse_flow_cell_directory_data(
            flow_cell_directory=flow_cell_directory_path,
            bcl_converter=bcl_converter,
        )

        self.store_flow_cell_in_status_db(parsed_flow_cell=parsed_flow_cell)

        self.add_flow_cell_data_to_housekeeper(
            flow_cell_name=parsed_flow_cell.id,
            flow_cell_directory=flow_cell_directory_path,
        )

        self.add_sample_lane_sequencing_metrics_for_flow_cell(
            flow_cell_directory=flow_cell_directory_path, bcl_converter=bcl_converter
        )

        flow_cell_sample_ids: List[str] = self.get_sample_ids_from_sample_sheet(
            parsed_flow_cell=parsed_flow_cell
        )

        self.update_sample_read_counts(sample_internal_ids=flow_cell_sample_ids)

        self.create_delivery_file_in_flow_cell_directory(
            flow_cell_directory=flow_cell_directory_path
        )

    def create_delivery_file_in_flow_cell_directory(self, flow_cell_directory: Path) -> None:
        Path(flow_cell_directory, DemultiplexingDirsAndFiles.DELIVERY).touch()

    def add_sample_lane_sequencing_metrics_for_flow_cell(
        self, flow_cell_directory: Path, bcl_converter: str
    ) -> None:
        sample_lane_sequencing_metrics: List[
            SampleLaneSequencingMetrics
        ] = create_sample_lane_sequencing_metrics_for_flow_cell(
            flow_cell_directory=flow_cell_directory,
            bcl_converter=bcl_converter,
        )

        self.status_db.session.add_all(sample_lane_sequencing_metrics)
        self.status_db.session.commit()

        LOG.info(f"Added sequencing metrics to status db for: {flow_cell_directory.name}")

    def get_sample_ids_from_sample_sheet(
        self, parsed_flow_cell: FlowCellDirectoryData
    ) -> List[str]:
        samples: List[FlowCellSample] = parsed_flow_cell.get_sample_sheet().samples
        sample_ids_with_indexes: List[str] = [sample.sample_id for sample in samples]
        return [sample_id_index.split("_")[0] for sample_id_index in sample_ids_with_indexes]

    def is_flow_cell_directory_valid(self, flow_cell_directory: Path) -> bool:
        """Validate that the flow cell directory exists and that the demultiplexing is complete."""

        if not flow_cell_directory.exists():
            LOG.warning(f"Flow cell directory does not exist: {flow_cell_directory}")
            return False

        if not self.is_demultiplexing_complete(flow_cell_directory=flow_cell_directory):
            LOG.warning(f"Demultiplexing is not complete for flow cell {flow_cell_directory.name}")
            return False

        return True

    def is_demultiplexing_complete(self, flow_cell_directory: Path) -> bool:
        return Path(flow_cell_directory, DemultiplexingDirsAndFiles.DEMUX_COMPLETE).exists()

    def update_sample_read_counts(self, sample_internal_ids: List[str]) -> None:
        """Update samples in status db with the sum of all read counts for the sample in the sequencing metrics table."""
        for sample_id in sample_internal_ids:
            self.update_single_sample_read_count(sample_id)
        self.status_db.session.commit()

    def update_single_sample_read_count(self, sample_id: str) -> None:
        sample = self.status_db.get_sample_by_internal_id(internal_id=sample_id)

        if sample:
            sample_read_count = self.status_db.get_number_of_reads_for_sample_from_metrics(
                sample_internal_id=sample_id
            )
            LOG.info(f"Updating sample {sample_id} with read count {sample_read_count}")
            sample.reads = sample_read_count

    def add_flow_cell_data_to_housekeeper(
        self, flow_cell_name: str, flow_cell_directory: Path
    ) -> None:
        LOG.info(f"Add flow cell data to Housekeeper for {flow_cell_name}")

        self.add_bundle_and_version_if_non_existent(flow_cell_name=flow_cell_name)

        tags: List[str] = [SequencingFileTag.FASTQ, SequencingFileTag.SAMPLE_SHEET, flow_cell_name]
        self.add_tags_if_non_existent(tag_names=tags)

        self.add_sample_sheet(
            flow_cell_directory=flow_cell_directory, flow_cell_name=flow_cell_name
        )
        self.add_sample_fastq_files(
            flow_cell_directory=flow_cell_directory, flow_cell_name=flow_cell_name
        )

    def add_sample_fastq_files(self, flow_cell_directory: Path, flow_cell_name: str) -> None:
        """Add sample fastq files from flow cell to Housekeeper."""
        fastq_file_paths: List[Path] = self.get_sample_fastq_paths_from_flow_cell(
            flow_cell_directory=flow_cell_directory
        )

        for fastq_file_path in fastq_file_paths:
            sample_id: str = self.get_sample_id_from_sample_fastq_file_path(
                fastq_file_path=fastq_file_path
            )

            if sample_id:
                self.add_file_if_non_existent(
                    file_path=fastq_file_path,
                    flow_cell_name=flow_cell_name,
                    tag_names=[SequencingFileTag.FASTQ, sample_id],
                )

    def add_sample_sheet(self, flow_cell_directory: Path, flow_cell_name: str) -> None:
        """Add sample sheet to Housekeeper."""
        self.add_file_if_non_existent(
            file_path=Path(flow_cell_directory, DemultiplexingDirsAndFiles.SAMPLE_SHEET_FILE_NAME),
            flow_cell_name=flow_cell_name,
            tag_names=[SequencingFileTag.SAMPLE_SHEET, flow_cell_name],
        )

    def is_valid_sample_fastq_filename(self, fastq_file_name: str) -> bool:
        """Validate the file name and discard any undetermined fastq files."""
        return "Undetermined" not in fastq_file_name

    def get_sample_fastq_paths_from_flow_cell(self, flow_cell_directory: Path) -> List[Path]:
        fastq_sample_pattern: str = (
            f"Unaligned*/Project_*/Sample_*/*{FileExtensions.FASTQ}{FileExtensions.GZIP}"
        )
        return list(flow_cell_directory.glob(fastq_sample_pattern))

    def get_sample_id_from_sample_fastq_file_path(self, fastq_file_path: Path) -> str:
        """Extract sample id from fastq file path."""
        sample_directory: str = fastq_file_path.parent.name
        directory_parts: str = sample_directory.split("_")

        if len(directory_parts) > 1:
            # The sample id is always the second part of the directory names
            return directory_parts[1]

        return directory_parts[0]

    def add_bundle_and_version_if_non_existent(self, flow_cell_name: str) -> None:
        """Add bundle if it does not exist."""
        if not self.hk_api.bundle(name=flow_cell_name):
            self.hk_api.create_new_bundle_and_version(name=flow_cell_name)

    def add_tags_if_non_existent(self, tag_names: List[str]) -> None:
        """Ensure that tags exist in Housekeeper."""
        for tag_name in tag_names:
            if self.hk_api.get_tag(name=tag_name) is None:
                self.hk_api.add_tag(name=tag_name)

    def add_file_if_non_existent(
        self, file_path: Path, flow_cell_name: str, tag_names: List[str]
    ) -> None:
        """Add file to Housekeeper if it has not already been added."""
        if not file_path.exists():
            LOG.warning(f"File does not exist: {file_path}")
            return

        if not self.file_exists_in_latest_version_for_bundle(
            file_path=file_path, flow_cell_name=flow_cell_name
        ):
            self.hk_api.add_and_include_file_to_latest_version(
                bundle_name=flow_cell_name,
                file=file_path,
                tags=tag_names,
            )

    def file_exists_in_latest_version_for_bundle(
        self, file_path: Path, flow_cell_name: str
    ) -> bool:
        """Check if file exists in latest version for bundle."""
        latest_version: Version = self.hk_api.get_latest_bundle_version(bundle_name=flow_cell_name)
        return any(
            file_path.name == Path(bundle_file.path).name for bundle_file in latest_version.files
        )

    def store_flow_cell_in_status_db(self, parsed_flow_cell: FlowCellDirectoryData) -> None:
        """Create flow cell from the parsed and validated flow cell data."""
        flow_cell: Flowcell = Flowcell(
            name=parsed_flow_cell.id,
            sequencer_type=parsed_flow_cell.sequencer_type,
            sequencer_name=parsed_flow_cell.machine_name,
            sequenced_at=parsed_flow_cell.run_date,
        )
        self.status_db.session.add(flow_cell)
        self.status_db.session.commit()

    def parse_flow_cell_directory_data(
        self, flow_cell_directory: Path, bcl_converter: str
    ) -> FlowCellDirectoryData:
        """Parse flow cell data from the flow cell directory."""
        if not self.is_flow_cell_directory_valid(flow_cell_directory=flow_cell_directory):
            raise FlowCellError(f"Flow cell directory not found: {flow_cell_directory}")

        try:
            flow_cell: FlowCellDirectoryData = FlowCellDirectoryData(
                flow_cell_path=flow_cell_directory, bcl_converter=bcl_converter
            )
            return flow_cell
        except FlowCellError as error:
            LOG.error(f"Unable to parse flow cell data from {flow_cell_directory}")
            raise error

    def get_bcl_converter_name(self, flow_cell_directory: Path) -> str:
        if self.is_bcl2fastq_demux_folder_structure(flow_cell_directory=flow_cell_directory):
            LOG.info("Flow cell was demultiplexed with bcl2fastq")
            return BclConverter.BCL2FASTQ
        LOG.info("Flow cell was demultiplexed with bcl_converter")
        return BclConverter.BCLCONVERT

    def is_bcl2fastq_demux_folder_structure(self, flow_cell_directory: Path) -> bool:
        """Check if flow cell directory is a Bcl2fastq demux folder structure."""

        for folder in flow_cell_directory.glob(pattern="*"):
            if re.search(DemultiplexingDirsAndFiles.BCL2FASTQ_TILE_DIR_PATTERN.value, str(folder)):
                return True
        return False


class DemuxPostProcessingHiseqXAPI(DemuxPostProcessingAPI):
    """Post demultiplexing API class for Hiseq X flow cell."""

    def add_to_cgstats(self, flow_cell_path: Path) -> None:
        """Add flow cell to cgstats."""
        LOG.info(
            f"{self.stats_api.binary} --database {self.stats_api.db_uri} add --machine X -u Unaligned {flow_cell_path.as_posix()}"
        )
        if self.dry_run:
            LOG.info("Dry run will not add flow cell stats")
            return
        cgstats_add_parameters = [
            "--database",
            self.stats_api.db_uri,
            "add",
            "--machine",
            "X",
            "-u",
            "Unaligned",
            flow_cell_path.as_posix(),
        ]
        cgstats_process: Process = Process(binary=self.stats_api.binary)
        cgstats_process.run_command(parameters=cgstats_add_parameters, dry_run=self.dry_run)

    def cgstats_select_project(self, flow_cell_id: str, flow_cell_path: Path) -> None:
        """Process selected project using cgstats."""
        unaligned_dir: Path = Path(flow_cell_path, DemultiplexingDirsAndFiles.UNALIGNED_DIR_NAME)
        for project_dir in unaligned_dir.glob("Project_*[0-9]*"):
            (_, project_id) = project_dir.name.split("_")
            stdout_file: Path = Path(
                flow_cell_path, "-".join(["stats", project_id, flow_cell_id]) + ".txt"
            )
            LOG.info(
                f"{self.stats_api.binary} --database {self.stats_api.db_uri} select --project {project_id} {flow_cell_id}"
            )
            if self.dry_run:
                LOG.info("Dry run will not process selected project")
                return
            cgstats_select_parameters: List[str] = [
                "--database",
                self.stats_api.db_uri,
                "select",
                "--project",
                project_id,
                flow_cell_id,
            ]
            cgstats_process: Process = Process(binary=self.stats_api.binary)
            with open(stdout_file.as_posix(), "w") as file:
                with redirect_stdout(file):
                    cgstats_process.run_command(
                        parameters=cgstats_select_parameters, dry_run=self.dry_run
                    )

    def cgstats_lanestats(self, flow_cell_path: Path) -> None:
        """Process lane stats using cgstats."""
        LOG.info(
            f"{self.stats_api.binary} --database {self.stats_api.db_uri} lanestats {flow_cell_path.as_posix()}"
        )
        if self.dry_run:
            LOG.info("Dry run will not add lane stats")
            return
        cgstats_lane_parameters: List[str] = [
            "--database",
            self.stats_api.db_uri,
            "lanestats",
            flow_cell_path.as_posix(),
        ]
        cgstats_process: Process = Process(binary=self.stats_api.binary)
        cgstats_process.run_command(parameters=cgstats_lane_parameters, dry_run=self.dry_run)

    def post_process_flow_cell(self, demux_results: DemuxResults) -> None:
        """Run all the necessary steps for post-processing a demultiplexed flow cell."""
        if not self.dry_run:
            Path(demux_results.flow_cell.path, DemultiplexingDirsAndFiles.DELIVERY).touch()
            # delete cgstats
        self.add_to_cgstats(flow_cell_path=demux_results.flow_cell.path)
        self.cgstats_select_project(
            flow_cell_id=demux_results.flow_cell.id, flow_cell_path=demux_results.flow_cell.path
        )
        self.cgstats_lanestats(flow_cell_path=demux_results.flow_cell.path)
        self.transfer_flow_cell(
            flow_cell_dir=demux_results.flow_cell.path, flow_cell_id=demux_results.flow_cell.id
        )

    def finish_flow_cell(
        self, bcl_converter: str, flow_cell_name: str, flow_cell_path: Path
    ) -> None:
        """Post-processing flow cell."""
        LOG.info(f"Check demultiplexed flow cell {flow_cell_name}")
        try:
            flow_cell: FlowCellDirectoryData = FlowCellDirectoryData(
                flow_cell_path=flow_cell_path, bcl_converter=bcl_converter
            )
        except FlowCellError:
            return
        demux_results: DemuxResults = DemuxResults(
            demux_dir=Path(self.demux_api.out_dir, flow_cell_name),
            flow_cell=flow_cell,
            bcl_converter=bcl_converter,
        )
        if not demux_results.flow_cell.is_hiseq_x_copy_completed():
            LOG.info(f"{flow_cell_name} is not yet completely copied")
            return
        if demux_results.flow_cell.is_hiseq_x_delivery_started():
            LOG.info(f"{flow_cell_name} copy is complete and delivery has already started")
            return
        if not demux_results.flow_cell.is_hiseq_x():
            LOG.info(f"{flow_cell_name} is not an Hiseq X flow cell")
            return
        LOG.info(f"{flow_cell_name} copy is complete and delivery will start")
        self.post_process_flow_cell(demux_results=demux_results)

    def finish_all_flow_cells(self, bcl_converter: str) -> None:
        """Loop over all flow cells and post process those that need it."""
        for flow_cell_dir in self.demux_api.get_all_demultiplexed_flow_cell_dirs():
            self.finish_flow_cell(
                bcl_converter=bcl_converter,
                flow_cell_name=flow_cell_dir.name,
                flow_cell_path=flow_cell_dir,
            )


class DemuxPostProcessingNovaseqAPI(DemuxPostProcessingAPI):
    """Post demultiplexing API class for Novaseq flow cell."""

    def rename_files(self, demux_results: DemuxResults) -> None:
        """Rename the files according to how we want to have it after demultiplexing is ready."""
        LOG.info(f"Renaming files for flow cell {demux_results.flow_cell.full_name}")
        flow_cell_id: str = demux_results.flow_cell.id
        for project_dir in demux_results.raw_projects:
            files.rename_project_directory(
                project_directory=project_dir, flow_cell_id=flow_cell_id, dry_run=self.dry_run
            )

    def add_to_cgstats(self, demux_results: DemuxResults) -> None:
        """Add the information from demultiplexing to cgstats"""
        create.create_novaseq_flowcell(manager=self.stats_api, demux_results=demux_results)

    def fetch_report_samples(self, flow_cell_id: str, project_name: str) -> List[StatsSample]:
        samples: List[StatsSample] = self.stats_api.find_handler.project_sample_stats(
            flowcell=flow_cell_id, project_name=project_name
        )
        LOG.info(
            "Found samples: %s for flow cell: %s, project: %s",
            ",".join(sample.sample_name for sample in samples),
            flow_cell_id,
            project_name,
        )
        return samples

    @staticmethod
    def sample_to_report_line(stats_sample: StatsSample, flow_cell_id: str) -> str:
        lanes: str = ",".join(str(lane) for lane in stats_sample.lanes)
        return "\t".join(
            [
                stats_sample.sample_name,
                flow_cell_id,
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
    def get_report_lines(stats_samples: List[StatsSample], flow_cell_id: str) -> Iterable[str]:
        """Convert stats samples to format lines ready to print."""
        for stats_sample in sorted(stats_samples, key=lambda x: x.sample_name):
            yield DemuxPostProcessingNovaseqAPI.sample_to_report_line(
                stats_sample=stats_sample, flow_cell_id=flow_cell_id
            )

    @staticmethod
    def write_report(report_path: Path, report_data: List[str]) -> None:
        LOG.info("Write demux report to %s", report_path)
        with report_path.open("w") as report_file:
            report_file.write("\t".join(STATS_HEADER) + "\n")
            for line in report_data:
                report_file.write(line + "\n")

    def get_report_data(self, flow_cell_id: str, project_name: Optional[str] = None) -> List[str]:
        """Fetch the lines that are used to make a report from a flow cell."""
        LOG.info(f"Fetch report data for flow cell: {flow_cell_id} project: {project_name}")
        project_samples: List[StatsSample] = self.fetch_report_samples(
            flow_cell_id=flow_cell_id, project_name=project_name
        )

        return list(self.get_report_lines(stats_samples=project_samples, flow_cell_id=flow_cell_id))

    def create_cgstats_reports(self, demux_results: DemuxResults) -> None:
        """Create a report for every project that was demultiplexed."""
        flow_cell_id: str = demux_results.flow_cell.id
        for project in demux_results.projects:
            project_name: str = project.split("_")[-1]
            report_data: List[str] = self.get_report_data(
                flow_cell_id=flow_cell_id, project_name=project_name
            )
            report_path: Path = demux_results.demux_dir / f"stats-{project_name}-{flow_cell_id}.txt"
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
            f"Copy sample sheet {demux_results.sample_sheet_path} from flow cell to demuxed result dir {demux_results.demux_sample_sheet_path}"
        )
        shutil.copy(
            demux_results.sample_sheet_path.as_posix(),
            demux_results.demux_sample_sheet_path.as_posix(),
        )

    def post_process_flow_cell(self, demux_results: DemuxResults) -> None:
        """Run all the necessary steps for post-processing a demultiplexed flow cell.
        This will
            1. Rename all the necessary files and folders
            2. Add the demux results to cgstats
            3. Produce reports for every project
            4. Generate a report with samples that have low cluster count
        """
        if demux_results.files_renamed():
            LOG.info("Files have already been renamed")
        else:
            # not needed
            self.rename_files(demux_results=demux_results)
        # depcrecated
        self.add_to_cgstats(demux_results=demux_results)
        # deprecated
        self.create_cgstats_reports(demux_results=demux_results)
        if demux_results.bcl_converter == "bcl2fastq":
            # relevant - topUnknownbarcodes
            self.create_barcode_summary_report(demux_results=demux_results)
        # moving not needed with new workflow   - on hold
        self.copy_sample_sheet(demux_results=demux_results)

        self.transfer_flow_cell(
            flow_cell_dir=demux_results.flow_cell.path, flow_cell_id=demux_results.flow_cell.id
        )

    def finish_flow_cell(
        self, flow_cell_name: str, bcl_converter: str, force: bool = False
    ) -> None:
        """Go through the post-processing steps for a flow cell.

        Force is used to finish a flow cell even if the files are renamed already.
        """
        LOG.info(
            f"Check demuxed flow cell {flow_cell_name}",
        )
        try:
            flow_cell: FlowCellDirectoryData = FlowCellDirectoryData(
                flow_cell_path=Path(self.demux_api.run_dir, flow_cell_name),
                bcl_converter=bcl_converter,
            )
        except FlowCellError:
            return
        if not self.demux_api.is_demultiplexing_completed(flow_cell=flow_cell):
            LOG.warning("Demultiplex is not ready for %s", flow_cell_name)
            return

        demux_results: DemuxResults = DemuxResults(
            demux_dir=Path(self.demux_api.out_dir, flow_cell_name),
            flow_cell=flow_cell,
            bcl_converter=bcl_converter,
        )
        if not demux_results.results_dir.exists():
            LOG.warning(f"Could not find results directory {demux_results.results_dir}")
            LOG.info(f"Can not finish flow cell {flow_cell_name}")
            return
        if demux_results.files_renamed():
            LOG.warning("Flow cell is already finished!")
            if not force:
                return
            LOG.info("Post processing flow cell anyway")
        self.post_process_flow_cell(demux_results=demux_results)

    def finish_all_flow_cells(self, bcl_converter: str) -> None:
        """Loop over all flow cells and post-process those that need it."""
        for flow_cell_dir in self.demux_api.get_all_demultiplexed_flow_cell_dirs():
            self.finish_flow_cell(flow_cell_name=flow_cell_dir.name, bcl_converter=bcl_converter)
