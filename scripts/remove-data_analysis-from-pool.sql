
ALTER TABLE `pool` DROP COLUMN `data_analysis`;
ALTER TABLE `pool` DROP COLUMN `sequenced_at`;
ALTER TABLE `pool` DROP COLUMN `invoiced_at`;
ALTER TABLE `pool` DROP COLUMN `lims_project`;
ALTER TABLE `pool` DROP COLUMN `reads`;

ALTER TABLE `family` CHANGE `data_delivery` `data_delivery` ENUM('analysis', 'analysis-bam', 'fastq', 'nipt-viewer', 'custom', 'scout')
 CHARACTER SET latin1
 COLLATE latin1_swedish_ci
 NULL
 DEFAULT NULL;

Update `family` SET data_delivery = 'fastq_qc' where data_delivery = 'custom';
