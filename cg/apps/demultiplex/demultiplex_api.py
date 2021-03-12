"""This api should handle everything around demultiplexing"""
import logging
from pathlib import Path
from typing import Iterable

LOG = logging.getLogger(__name__)

"""
for RUN_DIR in ${IN_DIR}/*; do
    if [[ ! -d ${RUN_DIR} ]]; then # -d means directory exists
        continue
    fi

    RUN=$(basename ${RUN_DIR})
    FC=${RUN##*_}
    FC=${FC:1}
    PROJECTLOG=${DEMUXES_DIR}/${RUN}/projectlog.$(date +'%Y%m%d%H%M%S').log

    if [[ -f ${RUN_DIR}/RTAComplete.txt && -f ${RUN_DIR}/CopyComplete.txt ]]; then
        if [[ ! -f ${RUN_DIR}/demuxstarted.txt ]]; then

            # start with a clean slate: remove empty sample sheets before continuing
            if [[ -e ${RUN_DIR}/SampleSheet.csv && ! -s ${RUN_DIR}/SampleSheet.csv  ]]; then
                rm ${RUN_DIR}/SampleSheet.csv
            fi

            if [[ ! -e ${RUN_DIR}/SampleSheet.csv ]]; then
                log "demux sheet fetch --application nova --pad --longest ${FC} > ${RUN_DIR}/SampleSheet.csv"
                demux sheet fetch --application nova --pad --longest ${FC} > ${RUN_DIR}/SampleSheet.csv
            fi

            # exit if samplesheet is still empty after running demux sheet fetch
            if [[ -e ${RUN_DIR}/SampleSheet.csv && ! -s ${RUN_DIR}/SampleSheet.csv ]]; then
                echo "Sample sheet empty! Exiting!" 1>&2
                continue
            fi

            log "mkdir -p ${DEMUXES_DIR}/${RUN}/"
            mkdir -p ${DEMUXES_DIR}/${RUN}/

            log "date +'%Y%m%d%H%M%S' > ${RUN_DIR}/demuxstarted.txt"
            date +'%Y%m%d%H%M%S' > ${RUN_DIR}/demuxstarted.txt

            log "bash ${SCRIPT_DIR}/demux-novaseq.bash ${RUN_DIR} ${DEMUXES_DIR} &>> ${PROJECTLOG}"
            bash ${SCRIPT_DIR}/demux-novaseq.bash ${RUN_DIR} ${DEMUXES_DIR} ${FC} ${PROJECTLOG} &>> ${PROJECTLOG}

            if [[ $? == 0 ]]; then
                # indicate demultiplexing is finished
                log "date +'%Y%m%d%H%M%S' > ${DEMUXES_DIR}/${RUN}/demuxcomplete.txt"
                date +'%Y%m%d%H%M%S' > ${DEMUXES_DIR}/${RUN}/demuxcomplete.txt
                # create trigger file for delivery script
                log "date +'%Y%m%d%H%M%S' > ${DEMUXES_DIR}/${RUN}/copycomplete.txt"
                date +'%Y%m%d%H%M%S' > ${DEMUXES_DIR}/${RUN}/copycomplete.txt
                # remove delivery.txt (if present) to trigger delivery
                log "date +'%Y%m%d%H%M%S' remove delivery.txt"
                rm -f date ${DEMUXES_DIR}/${RUN}/delivery.txt
            fi

            # This is an easy way to avoid running multiple demuxes at the same time
            break
        else
            log "${RUN} is finished and demultiplexing has already started"
        fi
    else
        log "${RUN} is not finished yet"
    fi
done
"""


def find_flowcells(in_path: Path) -> Iterable[Path]:
    """Loop over a directory and find all flowcell files

    It is assumed that the flowcell directories are situated as children to in_path
    """
    for child in in_path.iterdir():
        if not child.is_dir():
            continue
        LOG.info("Found directory %s", child)
        yield child


if __name__ == "__main__":
    cg_dir = Path("/Users/mans.magnusson/PycharmProjects/cg/cg/")
    for flowcell_directory in find_flowcells(cg_dir):
        print(type(flowcell_directory), flowcell_directory)
