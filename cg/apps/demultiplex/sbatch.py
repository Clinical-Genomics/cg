# This one needs run_dir, out_dir, basemask and sample_sheet

DEMULTIPLEX_COMMAND = """
singularity exec --bind \
/home/proj/production/demultiplexed-runs,\
/home/proj/production/flowcells/novaseq,\
/home/proj/production/flowcells/novaseq/'$SLURM_JOB_ID':/run/user/$(id -u) \
/home/proj/production/demux-on-hasta/novaseq/container/bcl2fastq_v2-20-0.sif \
bcl2fastq --loading-threads 3 --processing-threads 15 --writing-threads 3 \
--runfolder-dir {run_dir} --output-dir {out_dir} \
--sample-sheet {sample_sheet} \
--barcode-mismatches 1
touch {demux_completed_file}
"""

# This needs flowcell_name, email. logfile

DEMULTIPLEX_ERROR = """
mail -s 'ERROR demultiplexing of {flowcell_name}' {email} < '{logfile}'
"""
