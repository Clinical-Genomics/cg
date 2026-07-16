from pathlib import Path
from shutil import copy2


# TODO: write test
def copy_file(from_path: Path, to_path: Path) -> None:
    """Copy source file from_path to the destination to_path"""
    copy2(src=from_path, dst=to_path)
