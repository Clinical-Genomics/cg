ALTER TABLE `samples`
ADD COLUMN `data_analysis` varchar(64) DEFAULT NULL

ALTER TABLE `microbial_samples`
ADD COLUMN `data_analysis` varchar(64) DEFAULT NULL

ALTER TABLE `pools`
ADD COLUMN `data_analysis` varchar(64) DEFAULT NULL
