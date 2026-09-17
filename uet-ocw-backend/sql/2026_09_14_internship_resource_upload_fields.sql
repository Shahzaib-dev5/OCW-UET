ALTER TABLE `internship_resources`
    ADD COLUMN IF NOT EXISTS `description` TEXT NULL AFTER `resource_type`,
    ADD COLUMN IF NOT EXISTS `file_size` BIGINT UNSIGNED NULL AFTER `external_url`,
    ADD COLUMN IF NOT EXISTS `mime_type` VARCHAR(100) NULL AFTER `file_size`,
    ADD COLUMN IF NOT EXISTS `is_active` TINYINT(1) NOT NULL DEFAULT 1 AFTER `display_order`,
    ADD COLUMN IF NOT EXISTS `updated_at` TIMESTAMP NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP AFTER `created_at`;

CREATE INDEX IF NOT EXISTS `ix_internship_resources_resource_type`
    ON `internship_resources` (`resource_type`);
