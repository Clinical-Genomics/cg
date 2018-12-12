#!/bin/bash

set -e
shopt -s nullglob

FASTQ_DIR=${1?'Please provide a project directory.'}

RED="\033[0;31m"
RESET="\033[0m"

if [[ -f $FASTQ_DIR ]]; then
    echo >&2 "'${FASTQ_DIR}' is a file, not a directory. Aborting."
    exit 1
fi

for DIR in ${FASTQ_DIR}/*; do
    if [[ -d $DIR ]]; then
        for READ_DIRECTION in 1 2; do
            PATTERN="${DIR}/[1-8]_*_${READ_DIRECTION}_.fastq.gz"
            FASTQ_FILES=( ${PATTERN} )
            CONCAT_FILENAME=$(echo ${FASTQ_FILES[0]} | cut -d"_" -f 2,3,4,5,6,7,8)
            if [[ -z ${CONCAT_FILENAME} ]]; then
                continue
            fi
            echo "cat ${DIR}/[1-8]_*_${READ_DIRECTION}_.fastq.gz > ${DIR}/${CONCAT_FILENAME}"
            cat ${DIR}/[1-8]_*_${READ_DIRECTION}_.fastq.gz > ${DIR}/${CONCAT_FILENAME}
            BEFORE_SIZE=$(find ${DIR} -maxdepth 2 -type f -name "[1-8]_*_${READ_DIRECTION}_.fastq.gz" -exec du -ch {} + | grep total)
            AFTER_SIZE=$(du -ch ${DIR}/${CONCAT_FILENAME} | grep total)
            if [[ ${BEFORE_SIZE} != ${AFTER_SIZE} ]]; then
                echo "${RED}${BEFORE_SIZE} != ${AFTER_SIZE} ERROR!${RESET}"
            fi
            echo "rm -rf ${PATTERN}"
            rm -rf ${PATTERN}
        done
    fi
done
