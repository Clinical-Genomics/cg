ALTER TABLE `cg`.`flowcell` 
CHANGE COLUMN `sequencer_type` `sequencer_type` ENUM('hiseqga', 'hiseqx', 'novaseq') NULL DEFAULT NULL ;

