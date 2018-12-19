# -*- coding: utf-8 -*-
import datetime as dt
import logging
import shutil
from pathlib import Path
from typing import List

from coverage.python import os

log = logging.getLogger(__name__)


class FastqFileNameCreator:
    """Creates valid balsamic filename from the parameters"""

    @staticmethod
    def create(lane: int, flowcell: str, sample: str, read: int,
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

        with open(concat_file, 'wb') as wfd:
            for f in files:
                with open(f, 'rb') as fd:
                    shutil.copyfileobj(fd, wfd)


class FastqHandler:

    def __init__(self, config):
        self.root_dir = config['balsamic']['root']

    def link(self, family: str, sample: str, files: List):
        """Link FASTQ files for a balsamic sample.
        Shall be linked to /mnt/hds/proj/bionfo/BALSAMIC_ANALYSIS/case-id/fastq/"""

        wrk_dir = Path(f'{self.root_dir}/{family}/fastq')

        if wrk_dir.exists():
            shutil.rmtree(wrk_dir)

        wrk_dir.mkdir(parents=True, exist_ok=True)

        destination_paths_r1 = list()
        destination_paths_r2 = list()

        for fastq_data in files:
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
                concatenated_filename_r1 = fastq_name[2:]
            else:
                destination_paths_r2.append(destination_path)
                concatenated_filename_r2 = fastq_name[2:]

            if not destination_path.exists():
                log.info(f"linking: {fastq_path} -> {destination_path}")
                destination_path.symlink_to(fastq_path)
            else:
                log.debug(f"destination path already exists: {destination_path}")

        FastqFileConcatenator.concatenate(destination_paths_r1, f'{wrk_dir}/{concatenated_filename_r1}')
        FastqFileConcatenator.concatenate(destination_paths_r2, f'{wrk_dir}/{concatenated_filename_r2}')

        for myfile in destination_paths_r1:
            if os.path.isfile(myfile):
                os.remove(myfile)

        for myfile in destination_paths_r2:
            if os.path.isfile(myfile):
                os.remove(myfile)
