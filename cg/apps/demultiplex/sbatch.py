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
