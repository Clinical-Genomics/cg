ALTER TABLE `analysis`
ADD COLUMN `upload_started_at` datetime DEFAULT NULL;

UPDATE analysis
SET `upload_started_at` = uploaded_at;
