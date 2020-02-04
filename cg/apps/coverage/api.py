"""Chanjo API"""
from typing import List
import logging
import io
import json
from pathlib import Path

from cg.utils import Process

LOG = logging.getLogger(__name__)


class ChanjoAPI:

    """Interface to Chanjo, the coverage analysis tool."""

    def __init__(self, config: dict):

        self.chanjo_config = config["chanjo"]["config_path"]
        self.chanjo_binary = config["chanjo"]["binary_path"]
        self.process = Process(self.chanjo_binary, self.chanjo_config)

    def upload(
        self,
        sample_id: str,
        sample_name: str,
        group_id: str,
        group_name: str,
        bed_stream: io.TextIOWrapper,
    ):
        """Upload coverage for a sample."""

        source = str(Path(bed_stream.name).absolute())

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
            10,
            source,
        ]

        self.process.run_command(load_parameters)

    def sample(self, sample_id: str) -> dict:
        """Fetch sample from the database."""

        sample_parameters = ["db", "samples", "-s", sample_id]
        self.process.run_command(sample_parameters)
        samples = json.loads(self.process.stdout)

        for sample in samples:
            if sample["id"] == sample_id:
                return sample

        return None

    def delete_sample(self, sample_id: str):
        """Delete sample from database."""
        delete_parameters = ["db", "remove", sample_id]
        self.process.run_command(delete_parameters)

    def omim_coverage(self, samples: List[str]) -> dict:
        """Calculate omim coverage for samples"""

        omim_parameters = ["calculate", "coverage", "--omim"]
        for sample_id in samples:
            omim_parameters.extend(["-s", sample_id])
        self.process.run_command(omim_parameters)
        data = json.loads(self.process.stdout)
        return data

    def sample_coverage(self, sample_id: str, panel_genes: list) -> dict:
        """Calculate coverage for samples."""

        coverage_parameters = ["calculate", "coverage", "-s", sample_id]
        for gene_id in panel_genes:
            coverage_parameters.append(gene_id)
        self.process.run_command(coverage_parameters)
        data = json.loads(self.process.stdout).get(sample_id)
        return data
