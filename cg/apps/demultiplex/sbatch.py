# This one needs run_dir, out_dir, basemask and sample_sheet

DEMULTIPLEX_COMMAND = {
    "bcl2fastq": """
log "singularity exec --bind \
/home/proj/{environment}/demultiplexed-runs,\
/home/proj/{environment}/flowcells/novaseq,\
/home/proj/{environment}/flowcells/novaseq/'$SLURM_JOB_ID':/run/user/$(id -u) \
/home/proj/{environment}/demux-on-hasta/novaseq/container/bcl2fastq_v2-20-0.sif \
bcl2fastq --loading-threads 3 --processing-threads 15 --writing-threads 3 \
--runfolder-dir {run_dir} --output-dir {unaligned_dir} \
--sample-sheet {sample_sheet} \
--barcode-mismatches 1
touch {demux_completed_file}"

singularity exec --bind \
/home/proj/{environment}/demultiplexed-runs,\
/home/proj/{environment}/flowcells/novaseq,\
/home/proj/{environment}/flowcells/novaseq/'$SLURM_JOB_ID':/run/user/$(id -u) \
/home/proj/{environment}/demux-on-hasta/novaseq/container/bcl2fastq_v2-20-0.sif \
bcl2fastq --loading-threads 3 --processing-threads 15 --writing-threads 3 \
--runfolder-dir {run_dir} --output-dir {unaligned_dir} \
--sample-sheet {sample_sheet} \
--barcode-mismatches 1
touch {demux_completed_file}
log "bcl2fastq finished!"
""",
    "dragen": """
log "dragen --bcl-conversion-only true \
--bcl-input-directory {run_dir} \
--output-directory {unaligned_dir} \
--bcl-sampleproject-subdirectories true \
--force   
touch {demux_completed_file}"

dragen --bcl-conversion-only true \
--bcl-input-directory {run_dir} \
--output-directory {unaligned_dir} \
--bcl-sampleproject-subdirectories true \
--force   
touch {demux_completed_file}
log "Dragen BCL Convert finished!"
""",
}
# This needs flow cell id, email. logfile
DEMULTIPLEX_ERROR = """
mail -s 'ERROR demultiplexing of {flow_cell_id}' {email} < '{logfile}'
if [[ -e {demux_dir} ]]
then
    rm -r {demux_dir}
fi
if [[ -e {demux_started} ]]
then
    rm -r {demux_started}
fi
"""
