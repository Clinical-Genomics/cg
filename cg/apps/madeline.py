"""Code to handle madeline input and output"""
import logging
from tempfile import NamedTemporaryFile, mkdtemp
from typing import List

from cg.utils import Process

LOG = logging.getLogger(__name__)


def make_ped(family_id: str, samples: List[dict]):
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
            sex_gender.get(sample["sex"], "."),
            sample.get("father", "."),
            sample.get("mother", "."),
            "Y" if sample.get("deceased") else ".",
            "Y" if sample.get("proband") else ".",
            status_affected.get(sample.get("status"), "."),
        ]
        yield "\t".join(row)


def run(madeline_process: Process, ped_stream: List[str]):
    """Run madeline and generate a file with the results."""
    output_dir = mkdtemp()
    output_prefix = f"{output_dir}/madeline"
    out_path = f"{output_prefix}.xml"

    # write the input to a temp file
    with NamedTemporaryFile("w") as in_file:
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
        madeline_process.run_command(parameters=madeline_call)

    with open(out_path, "r") as output:
        svg_content = output.read()

    # strip away the script tag
    script_tag = '<script type="text/javascript" xlink:href=' '"javascript/madeline.js"></script>'
    svg_content.replace(script_tag, "")

    with open(out_path, "w") as out_handle:
        out_handle.write(svg_content)

    return out_path
