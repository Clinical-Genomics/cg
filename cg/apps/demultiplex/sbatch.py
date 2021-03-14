# This one needs run_dir, out_dir, basemask and sample_sheet

DEMULTIPLEX_COMMAND = """
singularity exec --bind \
/home/proj/production/demultiplexed-runs,\
/home/proj/production/flowcells/novaseq,\
/home/proj/production/flowcells/novaseq/'$SLURM_JOB_ID':/run/user/$(id -u) \
/home/proj/production/demux-on-hasta/novaseq/container/bcl2fastq_v2-20-0.sif \
bcl2fastq --loading-threads 3 --processing-threads 15 --writing-threads 3 \
--runfolder-dir {run_dir} --output-dir {out_dir} --use-bases-mask {basemask} \
--sample-sheet {sample_sheet} \
--barcode-mismatches 1
"""

# This needs flowcell_name, email. logfile

DEMULTIPLEX_ERROR = """
mail -s 'ERROR demultiplexing of {flowcell_name}' {email} < '{logfile}'
"""

if __name__ == "__main__":
    demux_params = {
        "run_dir": "path/to/a_flowcell/",
        "out_dir": "path/to/output_dir/",
        "basemask": "path/to/basemask.txt",
        "sample_sheet": "path/to/SampleSheet.csv",
    }
    print(DEMULTIPLEX_COMMAND.format(**demux_params))
    error_params = {
        "flowcell_name": "a_flowcell",
        "email": "clark.kent@mail.com",
        "logfile": "path/to/logfile.txt",
    }
    print(DEMULTIPLEX_ERROR.format(**error_params))
