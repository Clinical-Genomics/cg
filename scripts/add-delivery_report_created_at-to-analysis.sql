ALTER TABLE `analysis`
ADD COLUMN `delivery_report_created_at` datetime DEFAULT NULL;

ALTER TABLE `analysis` DROP COLUMN `delivered_at`;

ALTER TABLE `analysis` DROP COLUMN `housekeeper_id`;
