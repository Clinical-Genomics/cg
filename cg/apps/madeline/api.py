"""Madeline API"""
import logging
import pathlib
import tempfile
from typing import Iterable, List

from cg.utils import Process

LOG = logging.getLogger(__name__)


class MadelineAPI:
    """Interface to madeline, tool to generate pedigree pictures"""

    def __init__(self, config: dict):
        self.madeline_binary = str(pathlib.Path(config["madeline_exe"]).absolute())
        self.process = Process(self.madeline_binary)

    @staticmethod
    def make_ped(family_id: str, samples: List[dict]) -> Iterable[str]:
        """Yield lines that are used as madeline input."""
        columns = {
            "family": "FamilyId",
            "sample": "IndividualId",
            "sex": "Gender",
            "father": "Father",
            "mother": "Mother",
            "deceased": "Deceased",
            "proband": "Proband",
            "status": "Affected",
        }
        sex_gender = {"male": "M", "female": "F"}
        status_affected = {"affected": "Y", "unaffected": "N"}
        LOG.info("Generating madeline input lines")

        yield "\t".join(columns.values())

        for sample in samples:
            row = [
                family_id,
                sample["sample"],
                sex_gender.get(sample["sex"]) or ".",
                sample.get("father") or ".",
                sample.get("mother") or ".",
                "Y" if sample.get("deceased") else ".",
                "Y" if sample.get("proband") else ".",
                status_affected.get(sample.get("status")) or ".",
            ]
            yield "\t".join(row)

    @staticmethod
    def strip_script_tag(content: str) -> str:
        """Strip away a script tag from a string"""
        script_tag = (
            '<script type="text/javascript" xlink:href=' '"javascript/madeline.js"></script>'
        )
        return content.replace(script_tag, "")

    def run(self, family_id: str, samples: List[dict], out_path: str = None) -> pathlib.Path:
        """Run madeline and generate a file with the results."""
        if out_path:
            out_path = pathlib.Path(out_path)
        else:
            output_dir = pathlib.Path(tempfile.mkdtemp())
            out_path = output_dir / "madeline.xml"

        output_prefix = str(out_path.with_suffix(""))
        LOG.info("Generate madeline output to %s", out_path)

        ped_stream = self.make_ped(family_id, samples)

        # write the input to a temp file
        with tempfile.NamedTemporaryFile("w") as in_file:
            madeline_content = "\n".join(ped_stream)
            in_file.write(madeline_content)
            in_file.flush()
            madeline_call = [
                "--color",
                "--nolabeltruncation",
                "--outputprefix",
                output_prefix,
                in_file.name,
            ]
            self.process.run_command(parameters=madeline_call)

        with open(out_path, "r") as output:
            svg_content = output.read()

        svg_content = self.strip_script_tag(svg_content)

        with open(out_path, "w") as out_handle:
            out_handle.write(svg_content)

        return out_path

    def __repr__(self):
        return f"MadelineApi({self.madeline_binary})"
