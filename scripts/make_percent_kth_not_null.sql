UPDATE application SET percent_kth="" WHERE percent_kth IS NULL;
ALTER TABLE application MODIFY COLUMN percent_kth int NOT NULL;
