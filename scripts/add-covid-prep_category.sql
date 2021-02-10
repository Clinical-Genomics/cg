alter table `application` CHANGE `prep_category` `prep_category`
enum('cov','mic','rml','tgs','wes','wgs','wts') DEFAULT NULL;
