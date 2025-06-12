"""Module to handle NF executors."""

from datetime import datetime
from pathlib import Path
from typing import Iterable

from cg.apps.slurm.slurm_api import SlurmAPI
from cg.constants.constants import FileExtensions, FileFormat
from cg.constants.nextflow import JAVA_MEMORY_HEADJOB, NXF_JVM_ARGS_ENV, SlurmHeadJobDefaults
from cg.io.controller import ReadFile
from cg.models.slurm.sbatch import Sbatch
from cg.utils.utils import build_command_from_dict


class NfBaseHandler:
    """
    Parent class for handling the interaction with NF executors that are common to both Nextflow and NF-Tower.
    """

    pass


class NfTowerHandler(NfBaseHandler):
    """
    Parent class for handling the interaction with NF-Tower.
    """

    @classmethod
    def get_tower_launch_parameters(cls, tower_workflow: str, command_args: dict) -> list[str]:
        """Returns a tower launch command given a dictionary with arguments."""

        tower_options: list[str] = build_command_from_dict(
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
                    "stub_run",
                )
            },
            exclude_true=True,
        )
        return ["launch"] + tower_options + [tower_workflow]

    @classmethod
    def get_tower_relaunch_parameters(cls, from_tower_id: int, command_args: dict) -> list[str]:
        """Returns a tower relaunch command given a dictionary with arguments."""

        tower_options: list[str] = build_command_from_dict(
            options={
                f"--{arg.replace('_', '-')}": command_args.get(arg, None)
                for arg in (
                    "profile",
                    "params_file",
                    "config",
                    "compute_env",
                    "revision",
                    "stub_run",
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
        Workflow will be executed using tower
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

    @staticmethod
    def get_variables_to_export() -> dict[str, str]:
        """Dictionary with required environment variables to be exported."""
        return {NXF_JVM_ARGS_ENV: f"'{JAVA_MEMORY_HEADJOB}'"}

    @classmethod
    def get_nextflow_run_parameters(
        cls, case_id: str, workflow_bin_path: str, root_dir: str, command_args: dict
    ) -> list[str]:
        """Returns a Nextflow run command given a dictionary with arguments."""

        nextflow_options: list[str] = build_command_from_dict(
            options=dict((f"-{arg}", command_args.get(arg, True)) for arg in ("log", "config")),
            exclude_true=True,
        )
        run_options: list[str] = build_command_from_dict(
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
        return nextflow_options + ["run", workflow_bin_path] + run_options

    @staticmethod
    def get_head_job_sbatch_path(case_directory: Path) -> Path:
        """Path to Nextflow sbatch for the head job."""
        return Path(case_directory, "nextflow_head_job").with_suffix(FileExtensions.SBATCH)

    @classmethod
    def execute_head_job(
        cls,
        case_id: str,
        case_directory: Path,
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
            log_dir=case_directory.as_posix(),
            memory=memory,
            number_tasks=number_tasks,
            quality_of_service=qos,
        )

        sbatch_content: str = slurm_api.generate_sbatch_content(sbatch_parameters=sbatch_parameters)
        sbatch_path: Path = cls.get_head_job_sbatch_path(case_directory=case_directory)
        sbatch_number: int = slurm_api.submit_sbatch(
            sbatch_content=sbatch_content, sbatch_path=sbatch_path
        )
        return sbatch_number
