ALTER TABLE `application`
ADD COLUMN `min_sequencing_depth` int(11) DEFAULT NULL;

Update application SET min_sequencing_depth = sequencing_depth;

Update application SET min_sequencing_depth = sequencing_depth * 0.87
    where application.tag like 'WGS%'
