We loop over all flowcell directories and check if sequencing and transfering is done. This is indicated by the two
files RTAComplete.txt and CopyComplete.txt.
We also create file (demuxcomplete.txt) that indicates if is finished.

## Output to

`/home/proj/stage/demultiplexed-runs/`

## WHY DO WE NEED TO MAKE A DIFFERENCE BETWEEN FLUFFY AND WGS

    - we don't want to add dummy samples to fluffy sample sheet
    - We don't want to pad the fluffy indexes


Distinction can be made from that the 
    
    - index length for fluffy is 8 and wgs 10
    - read length for fluffy is 51 and 151 for wgs

### How the process is being done

- One cronjob creates the sample sheet 
- One cronjob starts demultiplexing
This can be done since the run parameters are ready before the rest of the data is in place

### THIS IS THE PART I DON'T UNDERSTAND ATM

- I think that the file delivery.txt indicates that demultiplexing has started.


- Then check if there is a SampleSheet.csv file, if not this is created by fetching raw information from LIMS and then
convert it to a format that bcl2fastq accepts.

- When that file exists we start demultiplexing by sending a batch job with instructions to slurm.

- Before starting demux we will need understand what basemask to use. Basemask is a value derived from the runparameters 
file. It has to do with the read length and the index length.

- Implement functionality for Novaseq and hiseq 2500, check for ApplicationName for hiseq or Application for novaseq 
in runParameters.
  
- If runparameters says index length should be 10 and index length is 8 we pad.

- In this case 160219_D00410_0217_AHJKMYBCXX the flowcell id is HJKMYBCXX

```bash
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
```
