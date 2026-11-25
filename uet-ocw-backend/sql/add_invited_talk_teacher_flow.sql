ALTER TABLE invited_talks
    ADD COLUMN owner_id BIGINT UNSIGNED NULL AFTER department_id,
    ADD COLUMN review_status VARCHAR(20) NOT NULL DEFAULT 'PENDING' AFTER display_order,
    ADD INDEX ix_invited_talks_owner_id (owner_id),
    ADD INDEX ix_invited_talks_review_status (review_status),
    ADD CONSTRAINT fk_invited_talks_owner
        FOREIGN KEY (owner_id) REFERENCES users(id) ON DELETE SET NULL;

UPDATE invited_talks
SET review_status = 'APPROVED'
WHERE status = 'PUBLISHED';
