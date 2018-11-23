ALTER TABLE `family_sample` CHANGE `status` `status` ENUM('affected','unaffected','unknown')
 CHARACTER SET latin1
 COLLATE latin1_swedish_ci
 NOT NULL
 DEFAULT 'unknown'
