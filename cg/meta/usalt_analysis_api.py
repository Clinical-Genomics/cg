""""Analysis logic for usalt"""
import gzip

from cg.apps.usalt import fastq
from cg.store import models


def link_sample(self, sample_obj: models.MicrobialSample):
    """Link FASTQ files for a sample."""
    file_objs = self.hk.files(bundle=sample_obj.internal_id, tags=['fastq'])
    files = []

    for file_obj in file_objs:

        # figure out flowcell name from header
        with gzip.open(file_obj.full_path) as handle:
            header_line = handle.readline().decode()
            header_info = self._fastq_header(header_line)
            lane = header_info['lane']
            flowcell = header_info['flowcell']
            readnumber = header_info['readnumber']

        data = {
            'path': file_obj.full_path,
            'lane': int(lane),
            'flowcell': flowcell,
            'read': int(readnumber),
            'undetermined': ('_Undetermined_' in file_obj.path),
        }
        # look for tile identifier (HiSeq X runs)
        matches = re.findall(r'-l[1-9]t([1-9]{2})_', file_obj.path)
        if len(matches) > 0:
            data['flowcell'] = f"{data['flowcell']}-{matches[0]}"
        files.append(data)

    # Decision for linking in Usalt structure if data_analysis contains Usalt
    fastq.link(case=sample_obj.microbial_order.internal_id,
               sample=sample_obj.internal_id, files=files)
