ALTER TABLE `application`
ADD COLUMN `min_sequencing_depth` int(11) DEFAULT NULL;

UPDATE application SET min_sequencing_depth = sequencing_depth;

UPDATE application SET min_sequencing_depth = 26
    WHERE application.tag LIKE 'WG%030';
