
ALTER TABLE `family` CHANGE `data_analysis` `data_analysis` ENUM('balsamic', 'fastq', 'fluffy', 'microsalt', 'mip-dna', 'mip-rna')
 CHARACTER SET latin1
 COLLATE latin1_swedish_ci
 NOT NULL;

ALTER TABLE `analysis` CHANGE `pipeline` `pipeline` ENUM('balsamic', 'fastq', 'fluffy', 'microsalt', 'mip-dna', 'mip-rna')
 CHARACTER SET latin1
 COLLATE latin1_swedish_ci
 NOT NULL;

# remove deprecated capture-kit from pool table
ALTER TABLE `pool` DROP COLUMN `capture_kit`;
