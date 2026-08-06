# This one needs run_dir, out_dir, basemask and sample_sheet

DEMULTIPLEX_COMMAND: str = """
log "dragen --bcl-conversion-only true \
--bcl-input-directory {run_dir} \
--output-directory {demux_dir} \
--force
touch {demux_completed_file}"

dragen --bcl-conversion-only true \
--bcl-input-directory {run_dir} \
--output-directory {demux_dir} \
--force
touch {demux_completed_file}
log "Dragen BCL Convert finished!"
"""

# This needs flow cell id, email, log_dir, run_name
DEMULTIPLEX_ERROR = """
LOGFILE="{log_dir}/{run_name}_$SLURM_JOB_ID.stderr"
mail -s 'ERROR demultiplexing of {flow_cell_id}' {email} < "$LOGFILE"
if [[ -e {demux_dir} ]]
then
    rm -r {demux_dir}
fi
if [[ -e {demux_started} ]]
then
    rm -r {demux_started}
fi
"""
