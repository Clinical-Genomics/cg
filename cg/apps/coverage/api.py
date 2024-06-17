"""Chanjo API"""

import logging
import requests
import tempfile

from cg.constants.constants import FileFormat
from cg.io.controller import ReadStream
from cg.utils import Process

LOG = logging.getLogger(__name__)


class ChanjoAPI:
    """Interface to Chanjo, the coverage analysis tool"""

    def __init__(self, config: dict):
        self.chanjo_config = config["chanjo"]["config_path"]
        self.chanjo_binary = config["chanjo"]["binary_path"]
        self.process = Process(binary=self.chanjo_binary, config=self.chanjo_config)

    def upload(
        self, sample_id: str, sample_name: str, group_id: str, group_name: str, bed_file: str
    ):
        """Upload coverage for a sample"""

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

    def sample(self, sample_id: str) -> dict | None:
        """Fetch sample from the database"""

        sample_parameters = ["db", "samples", "-s", sample_id]
        self.process.run_command(parameters=sample_parameters)
        samples: list = ReadStream.get_content_from_stream(
            file_format=FileFormat.JSON, stream=self.process.stdout
        )
        for sample in samples:
            if sample["id"] == sample_id:
                return sample
        return None

    def delete_sample(self, sample_id: str):
        """Delete sample from database"""
        delete_parameters = ["db", "remove", sample_id]
        self.process.run_command(parameters=delete_parameters)

    def omim_coverage(self, samples: list[dict]) -> dict:
        """Calculate OMIM coverage for samples"""

        omim_parameters = ["calculate", "coverage", "--omim"]
        for sample in samples:
            omim_parameters.extend(["-s", sample["id"]])
        self.process.run_command(parameters=omim_parameters)
        return ReadStream.get_content_from_stream(
            file_format=FileFormat.JSON, stream=self.process.stdout
        )

    def sample_coverage(self, sample_id: str, panel_genes: list) -> dict:
        """Calculate coverage for samples"""

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
        return ReadStream.get_content_from_stream(
            file_format=FileFormat.JSON, stream=self.process.stdout
        ).get(sample_id)


class Chanjo2API:
    """Interface to Chanjo2, the coverage analysis tool"""

    def __init__(self, base_url, config):
        self.base_url = base_url
        self.chanjo2_config = config["chanjo2"]["config_path"]
        self.chanjo2_binary = config["chanjo2"]["binary_path"]
        self.process = Process(binary=self.chanjo2_binary, config=self.chanjo2_config)

    def get_coverage_statistics(
        self, coverage_file_path, intervals_bed_path, completeness_thresholds
    ):
        endpoint = f"{self.base_url}/coverage/d4/interval_file/"
        headers = {"accept": "application/json", "Content-Type": "application/json"}
        payload = {
            "coverage_file_path": coverage_file_path,
            "intervals_bed_path": intervals_bed_path,
            "completeness_thresholds": completeness_thresholds,
        }

        response = requests.post(endpoint, headers=headers, json=payload)
        response.raise_for_status()

        return ReadStream.get_content_from_stream(file_format="json", stream=response.json())

    def sample_coverage(self, sample_id, panel_genes):
        pass


# Example usage:
if __name__ == "__main__":
    configuration = {
        "chanjo": {"config_path": "/path/to/chanjo/config", "binary_path": "/path/to/chanjo/binary"}
    }
    api = Chanjo2API(base_url="http://localhost:8000", configuration=config)
    coverage_file_path = "https://d4-format-testing.s3.us-west-1.amazonaws.com/hg002.d4"
    intervals_bed_path = "<path-to-109_green.bed>"
    completeness_thresholds = [10, 20, 30]

    try:
        result = api.get_coverage_statistics(
            coverage_file_path, intervals_bed_path, completeness_thresholds
        )
        print(result)
    except requests.exceptions.RequestException as e:
        print(f"An error occurred: {e}")

    try:
        local_result = api.run_local_coverage_calculation(sample_id, panel_genes)
        print(local_result)
    except Exception as e:
        print(f"An error occurred with local calculation: {e}")
