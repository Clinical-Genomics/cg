ALTER TABLE flowcell
MODIFY COLUMN status ENUM('ondisk', 'removed', 'requested', 'processing', 'retrieved');