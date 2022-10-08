"""Module for Nextflow Analysis API."""

import logging
from pathlib import Path
from typing import List
from datetime import datetime
import os
import operator
from cg.constants.constants import NFX_WORK_DIR, NFX_SAMPLE_HEADER
from cg.io.controller import ReadFile, WriteFile
from cg.constants.constants import FileFormat
from cg.exc import CgError

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
    def get_case_config_path(cls, case_id: str, root_dir: str) -> Path:
        """Generates a path where the Rnafusion sample sheet for the case_id should be located."""
        return Path((cls.get_case_path(case_id, root_dir)), case_id + "_samplesheet.csv")

    @classmethod
    def make_case_folder(cls, case_id: str, root_dir: str) -> None:
        """Make the case folder where analysis should be located."""
        os.makedirs(cls.get_case_path(case_id, root_dir), exist_ok=True)

    @classmethod
    def extract_read_files(cls, read_nb: int, metadata: list) -> list:
        sorted_metadata: list = sorted(metadata, key=operator.itemgetter("path"))
        return [d["path"] for d in sorted_metadata if d["read"] == read_nb]

    @classmethod
    def create_samplesheet_csv(
        cls, samplesheet_content: dict, headers: list, config_path: Path
    ) -> None:
        """Write sample sheet csv file."""
        with open(config_path, "w") as outfile:
            outfile.write(",".join(headers))
            for i in range(len(samplesheet_content[NFX_SAMPLE_HEADER])):
                outfile.write("\n")
                outfile.write(",".join([samplesheet_content[k][i] for k in headers]))

    @classmethod
    def get_verified_arguments_nextflow(
        cls, case_id: str, log: Path, pipeline: str, root_dir: str
    ) -> dict:
        """Transforms click argument related to nextflow that were left empty
        into defaults constructed with case_id paths."""

        return {
            "-log": NextflowAnalysisAPI.get_log_path(case_id, pipeline, root_dir, log),
        }

    @classmethod
    def get_log_path(cls, case_id: str, root_dir: str, pipeline: str, log: Path = None) -> Path:
        if log:
            return log
        launch_time: str = datetime.now().strftime("%Y-%m-%d_%H.%M.%S")
        return Path(
            cls.get_case_path(case_id, root_dir),
            case_id + "_" + pipeline + "_nextflow_log_" + launch_time + ".log",
        )

    @classmethod
    def get_workdir_path(cls, case_id: str, root_dir: str, work_dir: Path = None) -> Path:
        if work_dir:
            return work_dir
        return Path(cls.get_case_path(case_id, root_dir), NFX_WORK_DIR)

    @classmethod
    def get_input_path(cls, case_id: str, root_dir: str, input: Path = None) -> Path:
        if input:
            return input
        return Path(cls.get_case_config_path(case_id, root_dir))

    @classmethod
    def get_outdir_path(cls, case_id: str, root_dir: str, outdir: Path = None) -> Path:
        if outdir:
            return outdir
        return Path(cls.get_case_path(case_id, root_dir))

    @classmethod
    def get_nextflow_stdout_stderr(cls, case_id: str, root_dir: str) -> List[str]:
        return [
            " > "
            + str(cls.get_case_path(case_id=case_id, root_dir=root_dir))
            + "/"
            + case_id
            + "-stdout.log 2> "
            + str(cls.get_case_path(case_id=case_id, root_dir=root_dir))
            + "/"
            + case_id
            + "-stdout.err  < /dev/null & "
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
        return Path(cls.get_case_path(case_id, root_dir), case_id + "_deliverables.yaml")

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
