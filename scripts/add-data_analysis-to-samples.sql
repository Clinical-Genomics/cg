ALTER TABLE `sample`
ADD COLUMN `data_analysis` varchar(16) DEFAULT NULL;

ALTER TABLE `microbial_sample`
ADD COLUMN `data_analysis` varchar(16) DEFAULT NULL;

ALTER TABLE `pool`
ADD COLUMN `data_analysis` varchar(16) DEFAULT NULL;
