"""Module to read SampleSheet.csv files."""
import csv

from pathlib import Path
from typing import Dict, List
from cg.constants import FileExtensions
from cg.constants.symbols import COMMA
from cg.io.validate_path import validate_file_suffix


def read_sample_sheet(file_path: Path) -> Dict[str, List[str]]:
    """Read content in a SampleSheet.csv file."""
    validate_file_suffix(path_to_validate=file_path, target_suffix=FileExtensions.CSV)
    sample_sheet: Dict[str, List[str]] = {}
    with file_path.open("r") as f:
        reader = csv.reader(f, delimiter=COMMA)
        current_section = ""
        for row in reader:
            if row and row[0].startswith("[") and row != current_section:
                current_section = row[0]
                sample_sheet[current_section] = []
            elif row:
                sample_sheet[current_section].append(row)
    return sample_sheet
