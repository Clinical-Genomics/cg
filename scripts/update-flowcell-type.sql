update flowcell set sequencer_type = 'novaseq'
where substr(sequencer_name, 1, 3) = 'A00'
