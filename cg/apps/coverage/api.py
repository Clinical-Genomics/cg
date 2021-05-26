"""Chanjo API"""
import io
import json
import logging
import tempfile
from pathlib import Path
from typing import List, Optional

from cg.utils import Process

LOG = logging.getLogger(__name__)


class ChanjoAPI:

    """Interface to Chanjo, the coverage analysis tool."""

    def __init__(self, config: dict):

        self.chanjo_config = config["chanjo"]["config_path"]
        self.chanjo_binary = config["chanjo"]["binary_path"]
        self.process = Process(self.chanjo_binary, self.chanjo_config)

    def upload(
        self, sample_id: str, sample_name: str, group_id: str, group_name: str, bed_file: str
    ):
        """Upload coverage for a sample."""

        load_parameters = [
            "load",
            "--sample",
            sample_id,
            "--name",
            sample_name,
            "--group",
            group_id,
            "--group-name",
            group_name,
            "--threshold",
            "10",
            bed_file,
        ]

        self.process.run_command(parameters=load_parameters)

    def sample(self, sample_id: str) -> Optional[dict]:
        """Fetch sample from the database."""

        sample_parameters = ["db", "samples", "-s", sample_id]
        self.process.run_command(parameters=sample_parameters)
        samples = json.loads(self.process.stdout)

        for sample in samples:
            if sample["id"] == sample_id:
                return sample

        return None

    def delete_sample(self, sample_id: str):
        """Delete sample from database."""
        delete_parameters = ["db", "remove", sample_id]
        self.process.run_command(parameters=delete_parameters)

    def omim_coverage(self, samples: List[dict]) -> dict:
        """Calculate omim coverage for samples"""

        omim_parameters = ["calculate", "coverage", "--omim"]
        for sample in samples:
            omim_parameters.extend(["-s", sample["id"]])
        self.process.run_command(parameters=omim_parameters)
        return json.loads(self.process.stdout)

    def sample_coverage(self, sample_id: str, panel_genes: list) -> dict:
        """Calculate coverage for samples."""

        with tempfile.NamedTemporaryFile(mode="w+t") as tmp_gene_file:
            tmp_gene_file.write("\n".join([str(gene) for gene in panel_genes]))
            tmp_gene_file.flush()
            coverage_parameters = [
                "calculate",
                "coverage",
                "-s",
                sample_id,
                "-f",
                tmp_gene_file.name,
            ]
            self.process.run_command(parameters=coverage_parameters)
        data = json.loads(self.process.stdout).get(sample_id)
        return data
