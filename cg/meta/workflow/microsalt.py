import gzip
import logging
import re
from pathlib import Path
from typing import List, Any
from ruamel.yaml import safe_load

from requests.exceptions import HTTPError

from cg.apps import tb, hk, scoutapi, lims
from cg.apps.pipelines.fastqhandler import BaseFastqHandler
from cg.store import models, Store


class AnalysisAPI:
    """The pipelines are accessed through Trailblazer but cg provides additional conventions and
    hooks into the status database that makes managing analyses simpler"""

    def __init__(
        self,
        db: Store,
        hk_api: hk.HousekeeperAPI,
        lims_api: lims.LimsAPI,
        yaml_loader=safe_load,
        path_api=Path,
        logger=logging.getLogger(__name__),
    ):
        self.db = db
        self.hk = hk_api
        self.lims = lims_api
        self.yaml_loader = yaml_loader
        self.pather = path_api
        self.LOG = logger

    def check(self, family_obj: models.Family):
        """Check stuff before starting the analysis."""
        flowcells = self.db.flowcells(family=family_obj)
        statuses = []
        for flowcell_obj in flowcells:
            self.LOG.debug(f"{flowcell_obj.name}: checking flowcell")
            statuses.append(flowcell_obj.status)
            if flowcell_obj.status == "removed":
                self.LOG.info(f"{flowcell_obj.name}: requesting removed flowcell")
                flowcell_obj.status = "requested"
            elif flowcell_obj.status != "ondisk":
                self.LOG.warning(f"{flowcell_obj.name}: {flowcell_obj.status}")
        return all(status == "ondisk" for status in statuses)

    @staticmethod
    def fastq_header(line):
        """handle illumina's two different header formats
        @see https://en.wikipedia.org/wiki/FASTQ_format

        @HWUSI-EAS100R:6:73:941:1973#0/1

            HWUSI-EAS100R   the unique instrument name
            6   flowcell lane
            73  tile number within the flowcell lane
            941     'x'-coordinate of the cluster within the tile
            1973    'y'-coordinate of the cluster within the tile
            #0  index number for a multiplexed sample (0 for no indexing)
            /1  the member of a pair, /1 or /2 (paired-end or mate-pair reads only)

        Versions of the Illumina pipeline since 1.4 appear to use #NNNNNN
        instead of #0 for the multiplex ID, where NNNNNN is the sequence of the
        multiplex tag.

        With Casava 1.8 the format of the '@' line has changed:

        @EAS139:136:FC706VJ:2:2104:15343:197393 1:Y:18:ATCACG

            EAS139  the unique instrument name
            136     the run id
            FC706VJ     the flowcell id
            2   flowcell lane
            2104    tile number within the flowcell lane
            15343   'x'-coordinate of the cluster within the tile
            197393  'y'-coordinate of the cluster within the tile
            1   the member of a pair, 1 or 2 (paired-end or mate-pair reads only)
            Y   Y if the read is filtered, N otherwise
            18  0 when none of the control bits are on, otherwise it is an even number
            ATCACG  index sequence


        TODO: add unit test
        """

        rs = {"lane": None, "flowcell": None, "readnumber": None}

        parts = line.split(":")
        if len(parts) == 5:  # @HWUSI-EAS100R:6:73:941:1973#0/1
            rs["lane"] = parts[1]
            rs["flowcell"] = "XXXXXX"
            rs["readnumber"] = parts[-1].split("/")[-1]
        if len(parts) == 10:  # @EAS139:136:FC706VJ:2:2104:15343:197393 1:Y:18:ATCACG
            rs["lane"] = parts[3]
            rs["flowcell"] = parts[2]
            rs["readnumber"] = parts[6].split(" ")[-1]
        if len(parts) == 7:  # @ST-E00201:173:HCLCGALXX:1:2106:22516:34834/1
            rs["lane"] = parts[3]
            rs["flowcell"] = parts[2]
            rs["readnumber"] = parts[-1].split("/")[-1]

        return rs

    def link_sample(self, fastq_handler: BaseFastqHandler, sample: str, case: str):
        """Link FASTQ files for a sample."""
        file_objs = self.hk.files(bundle=sample, tags=["fastq"])
        files = []

        for file_obj in file_objs:
            # figure out flowcell name from header
            with gzip.open(file_obj.full_path) as handle:
                header_line = handle.readline().decode()
                header_info = self.fastq_header(header_line)

            data = {
                "path": file_obj.full_path,
                "lane": int(header_info["lane"]),
                "flowcell": header_info["flowcell"],
                "read": int(header_info["readnumber"]),
                "undetermined": ("_Undetermined_" in file_obj.path),
            }
            # look for tile identifier (HiSeq X runs)
            matches = re.findall(r"-l[1-9]t([1-9]{2})_", file_obj.path)
            if len(matches) > 0:
                data["flowcell"] = f"{data['flowcell']}-{matches[0]}"
            files.append(data)

        fastq_handler.link(case=case, sample=sample, files=files)
