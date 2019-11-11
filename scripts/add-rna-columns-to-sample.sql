ALTER TABLE `sample`
ADD COLUMN `from_sample` varchar(128) DEFAULT NULL;

ALTER TABLE `sample`
ADD COLUMN `time_point` INT(11) DEFAULT NULL;