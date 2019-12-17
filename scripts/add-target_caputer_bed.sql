CREATE TABLE `bed` (
  `id` int(11) NOT NULL AUTO_INCREMENT,
  `name` varchar(32) NOT NULL,
  `description` varchar(256) NOT NULL,
  `filename` varchar(256),
  `designer` varchar(256),
  `comment` text,
  `is_archived` tinyint(1) DEFAULT NULL,
  `created_at` datetime DEFAULT NULL,
  `updated_at` datetime DEFAULT NULL,
  PRIMARY KEY (`id`),
  UNIQUE KEY `name` (`name`)
) ENGINE=InnoDB AUTO_INCREMENT=1 DEFAULT CHARSET=latin1;

CREATE TABLE `bed_version` (
  `id` int(11) NOT NULL AUTO_INCREMENT,
  `version` int(11) NOT NULL,
  `genes` int(11) DEFAULT NULL,
  `unique_transcripts` int(11) DEFAULT NULL,
  `transcripts_with_all_exons_covered` int(11) DEFAULT NULL,
  `transcripts_with_at_least_one_exon_covered` int(11) DEFAULT NULL,
  `padding` int(11) DEFAULT NULL,
  `panel_size` int(11) DEFAULT NULL,
  `genome_version` varchar(32) NULL,
  `cosmic_snps` int(11) DEFAULT NULL,
  `non_genic_regions` int(11) DEFAULT NULL,
  `independent_segments` int(11) DEFAULT NULL,
  `comment` text,
  `created_at` datetime DEFAULT NULL,
  `updated_at` datetime DEFAULT NULL,
  `bed_id` int(11) NOT NULL,
  PRIMARY KEY (`id`),
  UNIQUE KEY `_app_version_uc` (`bed_id`,`version`),
  CONSTRAINT `bed_version_ibfk_1` FOREIGN KEY (`bed_id`) REFERENCES `bed` (`id`)
) ENGINE=InnoDB AUTO_INCREMENT=1 DEFAULT CHARSET=latin1;

ALTER TABLE sample
 ADD COLUMN  `bed_version_id` int(11);


INSERT INTO `bed` (`id`, `name`, `description`, `filename`, `designer`, `comment`, `is_archived`, `created_at`, `updated_at`)
VALUES
	(1,'GMCKsolid','GMCKsolid4.1','GMCKSolid4.1.bed','Johan Lindberg','',0,NULL,NULL),
	(2,'LymphoMATIC','LymphoMATIC2.1','LymphoMATIC2.1_hg19.bed','Christian Brieghel','',0,NULL,NULL),
	(3,'GMSmyeloid','GMSmyeloid5.1','GMSmyeloid5.1_hg19.bed','Christina Orsmark Pietras','',0,NULL,NULL),
	(4,'GMSLymphoid','GMSLymphoid7.1','GMSLymphoid7.1_hg19.bed','Christina Orsmark Pietras','',0,NULL,NULL),
	(5,'TwistWESRefseq','Whole exome and RefSeq','Twist_Target_hg19_RefSeq_1_22_X_Y.bed','Twist Bioscience','',0,NULL,NULL),
	(6,'TwistWholeExome','Whole exome','Twist_Target_hg19_whole_exome.bed','Twist Bioscience','',0,NULL,NULL),
	(7,'GIcfDNA','GIcfDNA3.1','GIcfDNA3.1_hg19.bed','Emma Tham','',0,NULL,NULL);

INSERT INTO `bed_version` (`id`, `version`, `genes`, `unique_transcripts`, `transcripts_with_all_exons_covered`, `transcripts_with_at_least_one_exon_covered`, `padding`, `panel_size`, `cosmic_snps`, `non_genic_regions`, `independent_segments`, `genome_version`, `created_at`, `updated_at`, `bed_id`)
VALUES
	(1,1,NULL,NULL,NULL,NULL,NULL,1705152,NULL,NULL,NULL,'hg19',NULL,NULL,1),
	(2,1,NULL,NULL,NULL,NULL,NULL,26548,NULL,NULL,NULL,'hg19',NULL,NULL,2),
	(3,1,NULL,NULL,NULL,NULL,NULL,712494,NULL,NULL,NULL,'hg19',NULL,NULL,3),
    (4,1,NULL,NULL,NULL,NULL,NULL,1957492,NULL,NULL,NULL,'hg19',NULL,NULL,4),
	(5,1,NULL,NULL,NULL,NULL,NULL,36339084,NULL,NULL,NULL,'hg19',NULL,NULL,5),
	(6,1,NULL,NULL,NULL,NULL,NULL,33053262,NULL,NULL,NULL,'hg19',NULL,NULL,6),
	(7,1,NULL,NULL,NULL,NULL,NULL,76261,NULL,NULL,NULL,'hg19',NULL,NULL,7);
