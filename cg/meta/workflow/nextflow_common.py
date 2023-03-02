"""Module for Nextflow Analysis API."""

import logging
import operator
import os
from datetime import datetime
from pathlib import Path
from subprocess import CalledProcessError
from typing import Any, Dict, List, Optional

from cg.constants.constants import FileFormat
from cg.constants.nextflow import NFX_SAMPLE_HEADER, NFX_WORK_DIR, NXF_PID_FILE_ENV
from cg.exc import CgError
from cg.io.controller import ReadFile, WriteFile

LOG = logging.getLogger(__name__)


class NextflowAnalysisAPI:
    """Handles communication between nextflow processes
    and the rest of CG infrastructure."""

    @classmethod
    def get_case_path(cls, case_id: str, root_dir: str) -> Path:
        """Returns a path where the rnafusion case should be located."""
        return Path(root_dir, case_id)

    @classmethod
    def verify_case_config_file_exists(cls, case_id: str, root_dir: str) -> None:
        if not Path(cls.get_case_config_path(case_id=case_id, root_dir=root_dir)).exists():
            raise ValueError(f"No config file found for case {case_id}")

    @classmethod
    def get_case_config_path(cls, case_id: str, root_dir: str) -> str:
        """Generates a path where the Rnafusion sample sheet for the case_id should be located."""
        return (
            Path((cls.get_case_path(case_id, root_dir)), f"{case_id}_samplesheet.csv")
            .absolute()
            .as_posix()
        )

    @classmethod
    def get_params_file_path(
        cls, case_id: str, root_dir: str, params_file: Optional[str] = None
    ) -> Path:
        """Return parameters file or a path where the Rnafusion default parameters file for a case id should be located."""
        if params_file:
            return Path(params_file).absolute()
        return Path(
            (cls.get_case_path(case_id, root_dir)), f"{case_id}_params_file.yaml"
        ).absolute()

    @classmethod
    def get_nextflow_config_path(cls, nextflow_config: Optional[str] = None) -> Optional[Path]:
        """Generates a path where the Nextflow configurations should be located."""
        if nextflow_config:
            return Path(nextflow_config).absolute()

    @classmethod
    def get_case_nextflow_pid_path(cls, case_id: str, root_dir: str) -> Path:
        """Generates a path where the Nextflow pid file for the case_id should be located."""
        # If not specified with the NXF_PID_FILE variable, a .nextflow.pid is created in the launch directory when
        # running nextflow in the background (with the bg option)
        return Path(
            (cls.get_case_path(case_id=case_id, root_dir=root_dir)), f"{case_id}_nextflow.pid"
        )

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
        return {
            NXF_PID_FILE_ENV: cls.get_case_nextflow_pid_path(
                case_id=case_id, root_dir=root_dir
            ).as_posix()
        }

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
    def extract_read_files(cls, read_nb: int, metadata: list) -> List[str]:
        sorted_metadata: list = sorted(metadata, key=operator.itemgetter("path"))
        return [d["path"] for d in sorted_metadata if d["read"] == read_nb]

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
    def get_verified_arguments_nextflow(
        cls,
        case_id: str,
        pipeline: str,
        root_dir: str,
        log: Path,
        bg: bool,
        quiet: bool,
        config: Optional[str],
    ) -> dict:
        """Transforms click argument related to nextflow that were left empty
        into defaults constructed with case_id paths."""

        return {
            "-bg": bg,
            "-quiet": quiet,
            "-log": cls.get_log_path(
                case_id=case_id, pipeline=pipeline, root_dir=root_dir, log=log
            ),
            "-config": cls.get_nextflow_config_path(nextflow_config=config),
        }

    @classmethod
    def get_verified_arguments_run(
        cls,
        case_id: str,
        root_dir: str,
        work_dir: str,
        resume: bool,
        profile: bool,
        with_tower: bool,
        stub: bool,
        params_file: Optional[str],
    ) -> dict:
        """Transforms click argument related to nextflow run that were left empty
        into defaults constructed with case_id paths."""
        return {
            "-w": cls.get_workdir_path(case_id=case_id, root_dir=root_dir, work_dir=work_dir),
            "-resume": resume,
            "-profile": profile,
            "-with-tower": with_tower,
            "-stub": stub,
            "-params-file": cls.get_params_file_path(
                case_id=case_id, root_dir=root_dir, params_file=params_file
            ),
        }

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

    @classmethod
    def get_input_path(cls, case_id: str, root_dir: str, input: str = None) -> Path:
        if input:
            return input
        return Path(cls.get_case_config_path(case_id, root_dir))

    @classmethod
    def get_outdir_path(cls, case_id: str, root_dir: str, outdir: str = None) -> Path:
        if outdir:
            return outdir
        return Path(cls.get_case_path(case_id, root_dir))

    @classmethod
    def get_nextflow_stdout_stderr(cls, case_id: str, root_dir: str) -> List[str]:
        case_path = cls.get_case_path(case_id, root_dir).as_posix()
        return [
            f" > {case_path}/{case_id}-stdout.log 2> {case_path}/{case_id}-stdout.err < /dev/null & "
        ]

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
    def verify_deliverables_file_exists(cls, case_id, root_dir):
        if not Path(cls.get_deliverables_file_path(case_id=case_id, root_dir=root_dir)).exists():
            raise CgError(f"No deliverables file found for case {case_id}")

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
