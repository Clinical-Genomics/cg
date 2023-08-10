"""Module to handle NF executors."""

from datetime import datetime
from pathlib import Path
from typing import Any, Dict, Iterable, List, Optional

from cg.apps.slurm.slurm_api import SlurmAPI
from cg.constants.constants import FileExtensions, FileFormat
from cg.constants.nextflow import (
    JAVA_MEMORY_HEADJOB,
    NFX_WORK_DIR,
    NXF_JVM_ARGS_ENV,
    SlurmHeadJobDefaults,
)
from cg.io.controller import ReadFile
from cg.models.slurm.sbatch import Sbatch
from cg.utils.utils import build_command_from_dict


class NfBaseHandler:
    """
    Parent class for handling the interaction with NF executors that are common to both Nextflow and NF-Tower.
    """

    @classmethod
    def get_case_path(cls, case_id: str, root_dir: str) -> Path:
        """Path to case directory."""
        return Path(root_dir, case_id)

    @classmethod
    def get_workdir_path(
        cls, case_id: str, root_dir: Path, work_dir: Optional[Path] = None
    ) -> Path:
        """Path to NF work directory."""
        if work_dir:
            return work_dir.absolute()
        return Path(cls.get_case_path(case_id, root_dir), NFX_WORK_DIR)

    @classmethod
    def write_nextflow_yaml(
        cls,
        content: Dict[str, Any],
        file_path: str,
    ) -> None:
        """Write Nextflow file with non-quoted booleans and quoted strings."""
        with open(file_path, "w") as outfile:
            for key, value in content.items():
                quotes = '"' if type(value) is str else ""
                outfile.write(f"{key}: {quotes}{value}{quotes}\n")


class NfTowerHandler(NfBaseHandler):
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


class NextflowHandler(NfBaseHandler):
    """
    Parent class for handling the interaction with Nextflow.
    """

    @classmethod
    def get_variables_to_export(cls, case_id: str, root_dir: str) -> Dict[str, str]:
        """Generates a dictionary with variables that needs to be exported."""
        return {NXF_JVM_ARGS_ENV: f"'{JAVA_MEMORY_HEADJOB}'"}

    @classmethod
    def get_nextflow_run_parameters(
        cls, case_id: str, pipeline_path: str, root_dir: str, command_args: dict
    ) -> List[str]:
        """Returns a Nextflow run command given a dictionary with arguments."""

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
        """Path to Nextflow log."""
        if log:
            return log
        launch_time: str = datetime.now().strftime("%Y-%m-%d_%H.%M.%S")
        return Path(
            cls.get_case_path(case_id, root_dir),
            f"{case_id}_{pipeline}_nextflow_{launch_time}",
        ).with_suffix(FileExtensions.LOG)

    @classmethod
    def get_head_job_sbatch_path(cls, case_id: str, root_dir: str) -> Path:
        """Path to Nextflow sbatch for the head job."""
        return Path(
            cls.get_case_path(case_id=case_id, root_dir=root_dir), "nextflow_head_job"
        ).with_suffix(FileExtensions.SBATCH)

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
        """Executes Nextflow head job command."""

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
        sbatch_path: Path = cls.get_head_job_sbatch_path(case_id=case_id, root_dir=root_dir)
        sbatch_number: int = slurm_api.submit_sbatch(
            sbatch_content=sbatch_content, sbatch_path=sbatch_path
        )
        return sbatch_number
