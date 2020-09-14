ALTER TABLE sample ADD COLUMN organism_id INTEGER NULL;

ALTER TABLE `sample`
ADD COLUMN `reference_genome` INT(11) DEFAULT NULL;

ALTER TABLE sample ADD CONSTRAINT `organism_ibfk_2` FOREIGN KEY (`organism_id`) REFERENCES `organism` (`id`);
