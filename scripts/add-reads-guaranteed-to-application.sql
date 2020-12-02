ALTER TABLE `application`
ADD COLUMN `reads_guaranteed` int(11) DEFAULT NULL;
UPDATE application SET reads_guaranteed = 75
