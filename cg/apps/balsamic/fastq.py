# -*- coding: utf-8 -*-
"""
This module handles concatenation of balsamic fastq files.

Classes:
    FastqFileNameCreator: Creates valid balsamic filenames
    FastqFileConcatenator: Handles file concatenation
    FastqHandler: Handles fastq file linking
"""
import datetime as dt
import logging
import shutil
from pathlib import Path
from typing import List

import os

loggger = logging.getLogger(__name__)


class FastqFileNameCreator:
    """Creates valid balsamic filename from the parameters"""

    @staticmethod
    def create(lane: str, flowcell: str, sample: str, read: str,
               undetermined: bool = False, date: dt.datetime = None,
               index: str = None) -> str:
        """Name a FASTQ file following Balsamic conventions. Naming must be
        xxx_R_1.fastq.gz and xxx_R_2.fastq.gz"""

        flowcell = f"{flowcell}-undetermined" if undetermined else flowcell
        date_str = date.strftime('%y%m%d') if date else '171015'
        index = index if index else 'XXXXXX'
        return f"{lane}_{date_str}_{flowcell}_{sample}_{index}_R_{read}.fastq.gz"


class FastqFileConcatenator:
    """Concatenates a list of files into one"""

    @staticmethod
    def concatenate(files: List, concat_file):
        """Concatenates a list of fastq files"""
        logger.info(FastqFileConcatenator.display_files(files, concat_file))

        with open(concat_file, 'wb') as wfd:
            for f in files:
                with open(f, 'rb') as fd:
                    shutil.copyfileobj(fd, wfd)

    @staticmethod
    def size_before(files: List):
        """returns the total size of the linked fastq files before concatenation"""

        return sum([os.stat(f).st_size for f in files])

    @staticmethod
    def size_after(concat_file):
        """returns the size of the concatenated fastq files"""

        return os.stat(concat_file).st_size

    @staticmethod
    def assert_file_sizes(size_before, size_after):
        """asserts the file sizes before and after concatenation"""
        msg = (
               f"Warning: file size difference after concatenation!"
               f"Before: {size_before} -> after: {size_after}"
              )

        assert size_before == size_after, msg
        logger.info('Concatenation file size check successful!')

    @staticmethod
    def display_files(files: List, concat_file):
        """display file names for logging purposes"""

        concat_file_name = Path(concat_file).name
        msg = f"Concatenating: {', '.join(Path(file_).name for file_ in files)} -> " \
            f"{concat_file_name}"

        return msg


class FastqHandler:
    """Handles fastq file linking"""

    def __init__(self, config):
        self.root_dir = config['balsamic']['root']

    def link(self, family: str, sample: str, files: List):
        """Link FASTQ files for a balsamic sample.
        Shall be linked to /mnt/hds/proj/bionfo/BALSAMIC_ANALYSIS/case-id/fastq/"""

        concatenator = FastqFileConcatenator()
        wrk_dir = Path(f'{self.root_dir}/{family}/fastq')

        wrk_dir.mkdir(parents=True, exist_ok=True)

        destination_paths_r1 = list()
        destination_paths_r2 = list()

        sorted_files = sorted(files, key=lambda k: k['path'])

        for fastq_data in sorted_files:
            fastq_path = Path(fastq_data['path'])
            fastq_name = FastqFileNameCreator.create(
                lane=fastq_data['lane'],
                flowcell=fastq_data['flowcell'],
                sample=sample,
                read=fastq_data['read'],
                undetermined=fastq_data['undetermined'],
            )

            destination_path = wrk_dir / fastq_name

            if fastq_data['read'] == 1:
                destination_paths_r1.append(destination_path)
                concatenated_filename_r1 = f"concatenated_{'_'.join(fastq_name.split('_')[-4:])}"
            else:
                destination_paths_r2.append(destination_path)
                concatenated_filename_r2 = f"concatenated_{'_'.join(fastq_name.split('_')[-4:])}"

            if not destination_path.exists():
                logger.info(f"linking: {fastq_path} -> {destination_path}")
                destination_path.symlink_to(fastq_path)
            else:
                log.debug(f"destination path already exists: {destination_path}")

        logger.info(f"Concatenation in progress for sample {sample}.")

        concatenator.concatenate(destination_paths_r1, f'{wrk_dir}/{concatenated_filename_r1}')
        size_before = concatenator.size_before(destination_paths_r1)
        size_after = concatenator.size_after(f'{wrk_dir}/{concatenated_filename_r1}')

        try:
            concatenator.assert_file_sizes(size_before, size_after)
        except AssertionError as error:
            logger.warning(error)

        concatenator.concatenate(destination_paths_r2, f'{wrk_dir}/{concatenated_filename_r2}')
        size_before = concatenator.size_before(destination_paths_r2)
        size_after = concatenator.size_after(f'{wrk_dir}/{concatenated_filename_r2}')

        try:
            concatenator.assert_file_sizes(size_before, size_after)
        except AssertionError as error:
            logger.warning(error)

        for myfile in destination_paths_r1:
            if os.path.isfile(myfile):
                os.remove(myfile)

        for myfile in destination_paths_r2:
            if os.path.isfile(myfile):
                os.remove(myfile)
