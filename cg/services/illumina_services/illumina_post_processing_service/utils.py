"""Utility functions for the Illumina post-processing service."""

from pathlib import Path

from cg.constants.demultiplexing import DemultiplexingDirsAndFiles


def create_delivery_file_in_flow_cell_directory(flow_cell_directory: Path) -> None:
    Path(flow_cell_directory, DemultiplexingDirsAndFiles.DELIVERY).touch()
