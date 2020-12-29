
ALTER TABLE `pool` DROP COLUMN `data_analysis`;
ALTER TABLE `pool` DROP COLUMN `sequenced_at`;
ALTER TABLE `pool` DROP COLUMN `invoiced_at`;
ALTER TABLE `pool` DROP COLUMN `lims_project`;
ALTER TABLE `pool` DROP COLUMN `reads`;

ALTER TABLE `family` CHANGE `data_delivery` `data_delivery` ENUM('fastq', 'custom', 'scout')
 CHARACTER SET latin1
 COLLATE latin1_swedish_ci
 NULL
 DEFAULT NULL;
