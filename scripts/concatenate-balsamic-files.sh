#!/bin/bash

set -e
shopt -s nullglob

FASTQ_DIR=${1?'Please provide a fastq directory.'}
SAMPLE_ID=${2?'Please provide a sample id.'}

RED="\033[0;31m"
RESET="\033[0m"

if [[ -f $FASTQ_DIR ]]; then
    echo >&2 "'${FASTQ_DIR}' is a file, not a directory. Aborting."
    exit 1
fi

for READ_DIRECTION in 1 2; do
    PATTERN="${FASTQ_DIR}/[1-8]_*_${SAMPLE_ID}_*_${READ_DIRECTION}_.fastq.gz"
    FASTQ_FILES=( ${PATTERN} )
    CONCAT_FILENAME=$(basename ${FASTQ_FILES[0]}) 
    CONCAT_FILENAME=${CONCAT_FILENAME:2}	

    if [[ -z ${CONCAT_FILENAME} ]]; then
	continue
    fi
    echo "cat ${FASTQ_DIR}/[1-8]_*_${SAMPLE_ID}_*_${READ_DIRECTION}_.fastq.gz > ${FASTQ_DIR}/${CONCAT_FILENAME}"
    cat ${FASTQ_DIR}/[1-8]_*_${SAMPLE_ID}_*_${READ_DIRECTION}_.fastq.gz > ${FASTQ_DIR}/${CONCAT_FILENAME}
    BEFORE_SIZE=$(find ${FASTQ_DIR} -maxdepth 1 -type l -name "[1-8]_*_${SAMPLE_ID}_*_${READ_DIRECTION}_.fastq.gz" -exec du -chL {} + | grep total)
    AFTER_SIZE=$(du -chL ${FASTQ_DIR}/${CONCAT_FILENAME} | grep total)
    if [[ ${BEFORE_SIZE} != ${AFTER_SIZE} ]]; then
	echo "${RED}${BEFORE_SIZE} != ${AFTER_SIZE} ERROR!${RESET}"
    fi
    
    echo "rm -rf ${PATTERN}"
    rm -rf ${PATTERN}
done
