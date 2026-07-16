import logging
from pathlib import Path

from cg.io.copy import copy_file

LOG = logging.getLogger(__name__)


# TODO: Make test
class RankModelFileCopier:

    @staticmethod
    def copy(source_snv_file: Path, source_sv_file: Path, case_run_directory: Path) -> None:
        """Copy rank model for Single Nucleotide Variant (SNV) and Structural Variation (SV) to the case_run_directory."""

        copy_file(from_path=source_snv_file, to_path=case_run_directory)
        LOG.info(f"Copied rank snv model file from {source_snv_file} into {case_run_directory}")

        copy_file(from_path=source_sv_file, to_path=case_run_directory)
        LOG.info(f"Copied rank sv model file from {source_sv_file} into {case_run_directory}")

        return None
