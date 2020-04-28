from pathlib import Path


class AnalysisAPI:
    """"""

    @staticmethod
    def get_deliverables_file_path(case_id, root_dir):
        return Path.joinpath(root_dir, case_id, "delivery_report", case_id + ".hk")

    @staticmethod
    def get_config_path(root_dir, case_id: str) -> Path:
        return Path.joinpath(root_dir, case_id, case_id + ".json")

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
