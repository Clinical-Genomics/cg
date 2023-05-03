"""Module for Rnafusion Analysis API."""

import logging
from pathlib import Path
from typing import Dict, List, Optional

from pydantic import ValidationError

from cg import resources
from cg.constants import Pipeline
from cg.constants.constants import FileFormat, WorkflowManager
from cg.constants.nextflow import NFX_READ1_HEADER, NFX_READ2_HEADER, NFX_SAMPLE_HEADER
from cg.constants.rnafusion import (
    RNAFUSION_METRIC_CONDITIONS,
    RNAFUSION_SAMPLESHEET_HEADERS,
    RNAFUSION_STRANDEDNESS_HEADER,
    RnafusionDefaults,
)
from cg.io.controller import WriteFile
from cg.io.json import read_json
from cg.meta.workflow.analysis import AnalysisAPI
from cg.meta.workflow.fastq import RnafusionFastqHandler
from cg.meta.workflow.nextflow_common import NextflowAnalysisAPI
from cg.meta.workflow.tower_common import TowerAnalysisAPI
from cg.models.cg_config import CGConfig
from cg.models.deliverables.metric_deliverables import MetricsBase, MultiqcDataJson
from cg.models.nextflow.deliverables import NextflowDeliverables, replace_dict_values
from cg.models.rnafusion.rnafusion_sample import RnafusionSample
from cg.utils import Process

LOG = logging.getLogger(__name__)


class RnafusionAnalysisAPI(AnalysisAPI):
    """Handles communication between RNAFUSION processes
    and the rest of CG infrastructure."""

    def __init__(
        self,
        config: CGConfig,
        pipeline: Pipeline = Pipeline.RNAFUSION,
    ):
        super().__init__(config=config, pipeline=pipeline)
        self.root_dir: str = config.rnafusion.root
        self.nfcore_pipeline_path: str = config.rnafusion.pipeline_path
        self.references: str = config.rnafusion.references
        self.profile: str = config.rnafusion.profile
        self.conda_env: str = config.rnafusion.conda_env
        self.conda_binary: str = config.rnafusion.conda_binary
        self.tower_binary_path: str = config.rnafusion.tower_binary_path
        self.tower_pipeline: str = config.rnafusion.tower_pipeline
        self.account: str = config.rnafusion.slurm.account
        self.email: str = config.rnafusion.slurm.mail_user
        self.compute_env: str = config.rnafusion.compute_env
        self.revision: str = config.rnafusion.revision

    @property
    def root(self) -> str:
        return self.root_dir

    @property
    def fastq_handler(self):
        return RnafusionFastqHandler

    @property
    def process(self):
        if not self._process:
            self._process = Process(
                binary=self.tower_binary_path,
            )
        return self._process

    @process.setter
    def process(self, process: Process):
        self._process = process

    def get_profile(self, profile: Optional[str] = None) -> str:
        if profile:
            return profile
        return self.profile

    def get_workflow_manager(self) -> str:
        """Get workflow manager for rnafusion."""
        return WorkflowManager.Tower.value

    def get_case_config_path(self, case_id):
        return NextflowAnalysisAPI.get_case_config_path(case_id=case_id, root_dir=self.root_dir)

    def verify_analysis_finished(self, case_id):
        return NextflowAnalysisAPI.verify_analysis_finished(case_id=case_id, root_dir=self.root_dir)

    @staticmethod
    def build_samplesheet_content(
        case_id: str, fastq_r1: List[str], fastq_r2: List[str], strandedness: str
    ) -> Dict[str, List[str]]:
        """Build samplesheet headers and lists"""
        try:
            RnafusionSample(
                sample=case_id, fastq_r1=fastq_r1, fastq_r2=fastq_r2, strandedness=strandedness
            )
        except ValidationError as error:
            LOG.error(error)
            raise ValueError

        samples_full_list: list = []
        strandedness_full_list: list = []
        # Complete sample and strandedness lists to the same length as fastq_r1:
        for _ in range(len(fastq_r1)):
            samples_full_list.append(case_id)
            strandedness_full_list.append(strandedness)

        samplesheet_content: dict = {
            NFX_SAMPLE_HEADER: samples_full_list,
            NFX_READ1_HEADER: fastq_r1,
            NFX_READ2_HEADER: fastq_r2,
            RNAFUSION_STRANDEDNESS_HEADER: strandedness_full_list,
        }
        return samplesheet_content

    def write_samplesheet(self, case_id: str, strandedness: str, dry_run: bool = False) -> None:
        """Write sample sheet for rnafusion analysis in case folder."""
        case_obj = self.status_db.get_case_by_internal_id(internal_id=case_id)
        if len(case_obj.links) != 1:
            raise NotImplementedError(
                "Case objects are assumed to be related to a single sample (one link)"
            )

        for link in case_obj.links:
            sample_metadata: List[str] = self.gather_file_metadata_for_sample(link.sample)
            fastq_r1: List[str] = NextflowAnalysisAPI.extract_read_files(1, sample_metadata)
            fastq_r2: List[str] = NextflowAnalysisAPI.extract_read_files(2, sample_metadata)
            samplesheet_content: Dict[str, List[str]] = self.build_samplesheet_content(
                case_id, fastq_r1, fastq_r2, strandedness
            )
            LOG.info(samplesheet_content)
            if dry_run:
                continue
            NextflowAnalysisAPI.create_samplesheet_csv(
                samplesheet_content=samplesheet_content,
                headers=RNAFUSION_SAMPLESHEET_HEADERS,
                config_path=NextflowAnalysisAPI.get_case_config_path(
                    case_id=case_id, root_dir=self.root_dir
                ),
            )

    def write_params_file(
        self, case_id: str, genomes_base: Optional[Path] = None, dry_run: bool = False
    ) -> None:
        """Write params-file for rnafusion analysis in case folder."""
        default_options: Dict[str, str] = self.get_default_parameters(case_id=case_id)
        if genomes_base:
            default_options["genomes_base"] = genomes_base
        LOG.info(default_options)
        if dry_run:
            return
        NextflowAnalysisAPI.write_nextflow_yaml(
            content=default_options,
            file_path=NextflowAnalysisAPI.get_params_file_path(
                case_id=case_id, root_dir=self.root_dir
            ),
        )

    def get_trailblazer_config_path(self, case_id: str) -> Path:
        """Return the path to a trailblazer config file containing Tower IDs."""
        return Path(self.root_dir, case_id, "tower_ids.yaml")

    def write_trailblazer_config(self, case_id: str, tower_id: str) -> None:
        """Write Tower IDs to a .YAML file used as the trailblazer config."""
        config_path = self.get_trailblazer_config_path(case_id=case_id)
        LOG.info(f"Writing Tower ID to {config_path.as_posix()}")
        WriteFile.write_file_from_content(
            content={case_id: [tower_id]},
            file_format=FileFormat.YAML,
            file_path=config_path,
        )

    def get_references_path(self, genomes_base: Optional[Path] = None) -> Path:
        if genomes_base:
            return genomes_base.absolute()
        return Path(self.references).absolute()

    def get_default_parameters(self, case_id: str) -> Dict:
        """Returns a dictionary with default RNAFusion parameters."""
        return {
            "input": NextflowAnalysisAPI.get_input_path(
                case_id=case_id, root_dir=self.root_dir
            ).as_posix(),
            "outdir": NextflowAnalysisAPI.get_outdir_path(
                case_id=case_id, root_dir=self.root_dir
            ).as_posix(),
            "genomes_base": self.get_references_path().as_posix(),
            "trim": RnafusionDefaults.TRIM,
            "fastp_trim": RnafusionDefaults.FASTP_TRIM,
            "trim_tail": RnafusionDefaults.TRIM_TAIL,
            "fusioninspector_filter": RnafusionDefaults.FUSIONINSPECTOR_FILTER,
            "fusionreport_filter": RnafusionDefaults.FUSIONREPORT_FILTER,
            "all": RnafusionDefaults.ALL,
            "pizzly": RnafusionDefaults.PIZZLY,
            "squid": RnafusionDefaults.SQUID,
            "starfusion": RnafusionDefaults.STARFUSION,
            "fusioncatcher": RnafusionDefaults.FUSIONCATCHER,
            "arriba": RnafusionDefaults.ARRIBA,
            "cram": RnafusionDefaults.CRAM,
            "priority": self.account,
            "clusterOptions": f"--qos={self.get_slurm_qos_for_case(case_id=case_id)}",
        }

    def config_case(
        self,
        case_id: str,
        strandedness: str,
        genomes_base: Path,
        dry_run: bool,
    ) -> None:
        """Create sample sheet file for RNAFUSION analysis."""
        NextflowAnalysisAPI.make_case_folder(
            case_id=case_id, root_dir=self.root_dir, dry_run=dry_run
        )
        LOG.info("Generating samplesheet")
        self.write_samplesheet(case_id=case_id, strandedness=strandedness, dry_run=dry_run)
        LOG.info("Generating parameters file")
        self.write_params_file(case_id=case_id, genomes_base=genomes_base, dry_run=dry_run)
        if dry_run:
            LOG.info("Dry run: Config files will not be written")
            return

        LOG.info("Configs files written")

    def run_analysis(
        self, case_id: str, command_args: dict, use_nextflow: bool, dry_run: bool = False
    ) -> None:
        """Execute RNAFUSION run analysis with given options."""
        if use_nextflow:
            self.process = Process(
                binary=self.config.rnafusion.binary_path,
                environment=self.conda_env,
                conda_binary=self.conda_binary,
                launch_directory=NextflowAnalysisAPI.get_case_path(
                    case_id=case_id, root_dir=self.root_dir
                ),
            )
            LOG.info("Pipeline will be executed using nextflow")
            parameters: List[str] = NextflowAnalysisAPI.get_nextflow_run_parameters(
                case_id=case_id,
                pipeline_path=self.nfcore_pipeline_path,
                root_dir=self.root_dir,
                command_args=command_args,
            )
            self.process.export_variables(
                export=NextflowAnalysisAPI.get_variables_to_export(
                    case_id=case_id, root_dir=self.root_dir
                ),
            )

            command = self.process.get_command(parameters=parameters)
            LOG.info(f"{command}")
            sbatch_number: int = NextflowAnalysisAPI.execute_head_job(
                case_id=case_id,
                root_dir=self.root_dir,
                slurm_account=self.account,
                email=self.email,
                qos=self.get_slurm_qos_for_case(case_id=case_id),
                commands=command,
                dry_run=dry_run,
            )
            LOG.info(f"Nextflow head job running as job {sbatch_number}")

        else:
            LOG.info("Pipeline will be executed using tower")
            parameters: List[str] = TowerAnalysisAPI.get_tower_launch_parameters(
                tower_pipeline=self.tower_pipeline,
                command_args=command_args,
            )
            self.process.run_command(parameters=parameters, dry_run=dry_run)
            if self.process.stderr:
                LOG.error(self.process.stderr)
            if not dry_run:
                tower_id = TowerAnalysisAPI.get_tower_id(stdout_lines=self.process.stdout_lines())
                self.write_trailblazer_config(case_id=case_id, tower_id=tower_id)
            LOG.info(self.process.stdout)

    def verify_case_config_file_exists(self, case_id: str) -> None:
        NextflowAnalysisAPI.verify_case_config_file_exists(case_id=case_id, root_dir=self.root_dir)

    def get_deliverables_file_path(self, case_id: str) -> Path:
        return NextflowAnalysisAPI.get_deliverables_file_path(
            case_id=case_id, root_dir=self.root_dir
        )

    def get_pipeline_version(self, case_id: str) -> str:
        return NextflowAnalysisAPI.get_pipeline_version(
            case_id=case_id, root_dir=self.root_dir, pipeline=self.pipeline
        )

    def verify_deliverables_file_exists(self, case_id: str) -> None:
        NextflowAnalysisAPI.verify_deliverables_file_exists(case_id=case_id, root_dir=self.root_dir)

    def report_deliver(self, case_id: str) -> None:
        """Get a deliverables file template from resources, parse it and, then write the deliverables file."""
        deliverables_content: dict = NextflowAnalysisAPI.get_template_deliverables_file_content(
            resources.RNAFUSION_BUNDLE_FILENAMES_PATH
        )
        try:
            for index, deliver_file in enumerate(deliverables_content):
                NextflowDeliverables(deliverables=deliver_file)
                deliverables_content[index] = replace_dict_values(
                    NextflowAnalysisAPI.get_replace_map(case_id=case_id, root_dir=self.root_dir),
                    deliver_file,
                )
        except ValidationError as error:
            LOG.error(error)
            raise ValueError
        NextflowAnalysisAPI.make_case_folder(case_id=case_id, root_dir=self.root_dir)
        NextflowAnalysisAPI.write_deliverables_bundle(
            deliverables_content=NextflowAnalysisAPI.add_bundle_header(
                deliverables_content=deliverables_content
            ),
            file_path=NextflowAnalysisAPI.get_deliverables_file_path(
                case_id=case_id, root_dir=self.root_dir
            ),
        )
        LOG.info(
            "Writing deliverables file in "
            + str(
                NextflowAnalysisAPI.get_deliverables_file_path(
                    case_id=case_id, root_dir=self.root_dir
                )
            )
        )

    def get_multiqc_json_path(self, case_id: str) -> Path:
        """Return the path of the multiqc_data.json file."""
        return Path(self.root_dir, case_id, "multiqc", "multiqc_data", "multiqc_data.json")

    def get_metrics_deliverables_path(self, case_id: str) -> Path:
        """Return a path where the <case>_metrics_deliverables.yaml file should be located."""
        return Path(self.root_dir, case_id, f"{case_id}_metrics_deliverables.yaml")

    def get_multiqc_json_metrics(self, case_id: str) -> List[MetricsBase]:
        """Get a multiqc_data.json file and returns metrics and values formatted."""
        multiqc_json: MultiqcDataJson = MultiqcDataJson(
            **read_json(file_path=self.get_multiqc_json_path(case_id=case_id))
        )
        metrics_values: Dict = {}
        for key in multiqc_json.report_general_stats_data:
            if case_id in key:
                metrics_values.update(list(key.values())[0])
        return [
            MetricsBase(
                header=None,
                id=case_id,
                input="multiqc_data.json",
                name=metric_name,
                step="multiqc",
                value=metric_value,
                condition=RNAFUSION_METRIC_CONDITIONS.get(metric_name, None),
            )
            for metric_name, metric_value in metrics_values.items()
        ]

    def write_metrics_deliverables(self, case_id: str, dry_run: bool = False):
        """Write <case>_metrics_deliverables.yaml file."""
        metrics_deliverables_path: Path = self.get_metrics_deliverables_path(case_id=case_id)
        if dry_run:
            LOG.info(
                f"Dry run: metrics deliverables file would be written to {metrics_deliverables_path.as_posix()}"
            )
            return
        LOG.info(f"Writing metrics deliverables file to {metrics_deliverables_path.as_posix()}")
        WriteFile.write_file_from_content(
            content={
                "metrics": [
                    metric.dict() for metric in self.get_multiqc_json_metrics(case_id=case_id)
                ]
            },
            file_format=FileFormat.YAML,
            file_path=metrics_deliverables_path,
        )
