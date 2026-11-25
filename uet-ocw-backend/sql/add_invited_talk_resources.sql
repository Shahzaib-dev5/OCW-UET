CREATE TABLE invited_talk_resources (
    id BIGINT UNSIGNED NOT NULL AUTO_INCREMENT,
    talk_id BIGINT UNSIGNED NOT NULL,
    title VARCHAR(255) NOT NULL,
    resource_type VARCHAR(30) NOT NULL DEFAULT 'LINK',
    url VARCHAR(1000) NOT NULL,
    description TEXT NULL,
    display_order INT NOT NULL DEFAULT 0,
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    updated_at DATETIME DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    PRIMARY KEY (id),
    INDEX ix_invited_talk_resources_talk_id (talk_id),
    CONSTRAINT fk_invited_talk_resources_talk FOREIGN KEY (talk_id)
        REFERENCES invited_talks(id) ON DELETE CASCADE
);
