"""Module to handle NF executors."""

import logging
import operator
import os
from datetime import datetime
from pathlib import Path
from subprocess import CalledProcessError
from typing import Any, Dict, Iterable, List, Optional

from cg.apps.slurm.slurm_api import SlurmAPI
from cg.constants.constants import FileFormat
from cg.constants.nextflow import (
    JAVA_MEMORY_HEADJOB,
    NFX_SAMPLE_HEADER,
    NFX_WORK_DIR,
    NXF_JVM_ARGS_ENV,
    SlurmHeadJobDefaults,
)
from cg.io.controller import ReadFile, WriteFile
from cg.models.slurm.sbatch import Sbatch
from cg.utils.utils import build_command_from_dict

LOG = logging.getLogger(__name__)


class NfHandler:
    """
    Parent class for handling the interaction with NF executors.
    """

    pass


class NfTowerHandler(NfHandler):
    """
    Parent class for handling the interaction with NF-Tower.
    """

    @classmethod
    def get_tower_launch_parameters(cls, tower_pipeline: str, command_args: dict) -> List[str]:
        """Returns a tower launch command given a dictionary with arguments."""

        tower_options: List[str] = build_command_from_dict(
            options={
                f"--{arg.replace('_', '-')}": command_args.get(arg, None)
                for arg in (
                    "work_dir",
                    "profile",
                    "params_file",
                    "config",
                    "name",
                    "revision",
                    "compute_env",
                )
            },
            exclude_true=True,
        )
        return ["launch"] + tower_options + [tower_pipeline]

    @classmethod
    def get_tower_relaunch_parameters(cls, from_tower_id: int, command_args: dict) -> List[str]:
        """Returns a tower relaunch command given a dictionary with arguments."""

        tower_options: List[str] = build_command_from_dict(
            options={
                f"--{arg.replace('_', '-')}": command_args.get(arg, None)
                for arg in (
                    "profile",
                    "params_file",
                    "config",
                    "compute_env",
                )
            },
            exclude_true=True,
        )
        now: str = datetime.now().strftime("%Y%m%d%H%M%S")
        return [
            "runs",
            "relaunch",
            "--id",
            str(from_tower_id),
            "--name",
            f"{command_args.get('name')}_from{str(from_tower_id)}_{now}",
        ] + tower_options

    @staticmethod
    def get_tower_id(stdout_lines: Iterable) -> str:
        """Parse the stdout and return a workflow id. An example of the output to parse is:
        Case <CASE_ID> exists in status db
        Running RNAFUSION analysis for <CASE_ID>
        Pipeline will be executed using tower
        Running command <COMMAND>

          Workflow 1uxZE9JM7Tl58r submitted at [<WORKSPACE>] workspace.

        https://<URL_TO_TOWER_CASE>
        Action running set for case <CASE_ID>"""
        for line in stdout_lines:
            if line.strip().startswith("Workflow"):
                return line.strip().split()[1]

    @classmethod
    def get_last_tower_id(cls, case_id: str, trailblazer_config: Path) -> int:
        """Return the previously-stored NF-Tower ID."""
        if not trailblazer_config.exists():
            raise FileNotFoundError(f"No NF-Tower ID found for case {case_id}.")
        return ReadFile.get_content_from_file(
            file_format=FileFormat.YAML, file_path=trailblazer_config
        ).get(case_id)[-1]


class NextflowHandler(NfHandler):
    """
    Parent class for handling the interaction with Nextflow.
    """

    @classmethod
    def get_case_path(cls, case_id: str, root_dir: str) -> Path:
        """Returns a path where the rnafusion case should be located."""
        return Path(root_dir, case_id)

    @classmethod
    def get_case_config_path(cls, case_id: str, root_dir: str) -> str:
        """Return a path where the sample sheet for the case_id should be located."""
        return (
            Path((cls.get_case_path(case_id, root_dir)), f"{case_id}_samplesheet.csv")
            .absolute()
            .as_posix()
        )

    @classmethod
    def get_nextflow_config_path(cls, nextflow_config: Optional[str] = None) -> Optional[Path]:
        """Generates a path where the Nextflow configurations should be located."""
        if nextflow_config:
            return Path(nextflow_config).absolute()

    @classmethod
    def get_software_version_path(cls, case_id: str, root_dir: str) -> Path:
        return Path(
            (cls.get_case_path(case_id, root_dir)), "pipeline_info", "software_versions.yml"
        )

    @classmethod
    def get_pipeline_version(cls, case_id: str, root_dir: str, pipeline: str) -> str:
        try:
            with open(
                cls.get_software_version_path(case_id=case_id, root_dir=root_dir), "r"
            ) as file:
                last_line = file.readlines()[-1]
            return last_line.split(" ")[-1]
        except (Exception, CalledProcessError):
            LOG.warning(f"Could not retrieve {pipeline} workflow version!")
            return "0.0.0"

    @classmethod
    def get_variables_to_export(cls, case_id: str, root_dir: str) -> Dict[str, str]:
        """Generates a dictionary with variables that needs to be exported."""
        return {NXF_JVM_ARGS_ENV: f"'{JAVA_MEMORY_HEADJOB}'"}

    @classmethod
    def verify_analysis_finished(cls, case_id: str, root_dir: str) -> None:
        if not Path(cls.get_software_version_path(case_id=case_id, root_dir=root_dir)).exists():
            raise ValueError(
                f"Analysis not finished: pipeline_info/software_versions.yml file not found for case {case_id}"
            )

    @classmethod
    def make_case_folder(cls, case_id: str, root_dir: str, dry_run: bool = False) -> None:
        """Make the case folder where analysis should be located."""
        if not dry_run:
            os.makedirs(cls.get_case_path(case_id=case_id, root_dir=root_dir), exist_ok=True)

    @classmethod
    def extract_read_files(
        cls, metadata: list, forward: bool = False, reverse: bool = False
    ) -> List[str]:
        """Extract a list of fastq file paths for either forward or reverse reads."""
        if forward and not reverse:
            read_number = 1
        elif reverse and not forward:
            read_number = 2
        else:
            raise ValueError("Either forward or reverse needs to be specified")
        sorted_metadata: list = sorted(metadata, key=operator.itemgetter("path"))
        return [d["path"] for d in sorted_metadata if d["read"] == read_number]

    @classmethod
    def create_samplesheet_csv(
        cls,
        samplesheet_content: Dict[str, List[str]],
        headers: List[str],
        config_path: Path,
    ) -> None:
        """Write sample sheet csv file."""
        with open(config_path, "w") as outfile:
            outfile.write(",".join(headers))
            for i in range(len(samplesheet_content[NFX_SAMPLE_HEADER])):
                outfile.write("\n")
                outfile.write(",".join([samplesheet_content[k][i] for k in headers]))

    @classmethod
    def write_nextflow_yaml(
        cls,
        content: Dict[str, Any],
        file_path: str,
    ) -> None:
        """Write nextflow file with non-quoted booleans and quoted strings."""
        with open(file_path, "w") as outfile:
            for key, value in content.items():
                quotes = '"' if type(value) is str else ""
                outfile.write(f"{key}: {quotes}{value}{quotes}\n")

    @classmethod
    def get_nextflow_run_parameters(
        cls, case_id: str, pipeline_path: str, root_dir: str, command_args: dict
    ) -> List[str]:
        """Returns a nextflow run command given a dictionary with arguments."""

        nextflow_options: List[str] = build_command_from_dict(
            options=dict((f"-{arg}", command_args.get(arg, True)) for arg in ("log", "config")),
            exclude_true=True,
        )
        run_options: List[str] = build_command_from_dict(
            options=dict(
                (f"-{arg.replace('_', '-')}", command_args.get(arg, None))
                for arg in (
                    "work_dir",
                    "resume",
                    "profile",
                    "with_tower",
                    "params_file",
                )
            ),
            exclude_true=True,
        )
        return nextflow_options + ["run", pipeline_path] + run_options

    @classmethod
    def get_log_path(cls, case_id: str, pipeline: str, root_dir: str, log: str = None) -> Path:
        if log:
            return log
        launch_time: str = datetime.now().strftime("%Y-%m-%d_%H.%M.%S")
        return Path(
            cls.get_case_path(case_id, root_dir),
            f"{case_id}_{pipeline}_nextflow_log_{launch_time}.log",
        )

    @classmethod
    def get_workdir_path(cls, case_id: str, root_dir: str, work_dir: str = None) -> Path:
        if work_dir:
            return work_dir
        return Path(cls.get_case_path(case_id, root_dir), NFX_WORK_DIR)

    # @classmethod
    # def get_input_path(cls, case_id: str, root_dir: str, input: str = None) -> Path:
    #     if input:
    #         return input
    #     return Path(cls.get_case_config_path(case_id, root_dir))

    @classmethod
    def get_outdir_path(cls, case_id: str, root_dir: str, outdir: str = None) -> Path:
        if outdir:
            return outdir
        return Path(cls.get_case_path(case_id, root_dir))

    @classmethod
    def get_replace_map(cls, case_id: str, root_dir: str) -> dict:
        return {
            "PATHTOCASE": str(cls.get_case_path(case_id, root_dir)),
            "CASEID": case_id,
        }

    @classmethod
    def get_deliverables_file_path(cls, case_id: str, root_dir: str) -> Path:
        """Returns a path where the rnafusion deliverables file for the case_id should be located."""
        return Path(cls.get_case_path(case_id, root_dir), f"{case_id}_deliverables.yaml")

    @classmethod
    def get_template_deliverables_file_content(cls, file_bundle_template: Path) -> dict:
        """Read deliverables file template and return content."""
        return ReadFile.get_content_from_file(
            file_format=FileFormat.YAML,
            file_path=file_bundle_template,
        )

    @classmethod
    def add_bundle_header(cls, deliverables_content: dict) -> dict:
        return {"files": deliverables_content}

    @classmethod
    def write_deliverables_bundle(
        cls, deliverables_content: dict, file_path: Path, file_format=FileFormat.YAML
    ) -> None:
        WriteFile.write_file_from_content(
            content=deliverables_content, file_format=file_format, file_path=file_path
        )

    @classmethod
    def get_sbatch_path(cls, case_id: str, root_dir: str) -> Path:
        """Returns a path where the nextflow sbatch for the head job should be located."""
        return Path(
            cls.get_case_path(case_id=case_id, root_dir=root_dir), "nextflow_head_job.sbatch"
        )

    @classmethod
    def execute_head_job(
        cls,
        case_id: str,
        root_dir: str,
        slurm_account: str,
        email: str,
        qos: str,
        commands: str,
        hours: int = SlurmHeadJobDefaults.HOURS,
        memory: int = SlurmHeadJobDefaults.MEMORY,
        number_tasks: int = SlurmHeadJobDefaults.NUMBER_TASKS,
        dry_run: bool = False,
    ) -> int:
        """Executes nextflow head job command."""

        slurm_api: SlurmAPI = SlurmAPI()
        slurm_api.set_dry_run(dry_run=dry_run)
        sbatch_parameters: Sbatch = Sbatch(
            account=slurm_account,
            commands=commands,
            email=email,
            hours=hours,
            job_name=f"{case_id}.%j",
            log_dir=cls.get_case_path(case_id=case_id, root_dir=root_dir).as_posix(),
            memory=memory,
            number_tasks=number_tasks,
            quality_of_service=qos,
        )

        sbatch_content: str = slurm_api.generate_sbatch_content(sbatch_parameters=sbatch_parameters)
        sbatch_path: Path = cls.get_sbatch_path(case_id=case_id, root_dir=root_dir)
        sbatch_number: int = slurm_api.submit_sbatch(
            sbatch_content=sbatch_content, sbatch_path=sbatch_path
        )
        return sbatch_number
