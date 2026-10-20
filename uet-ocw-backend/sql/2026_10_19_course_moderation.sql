-- Additive, rerunnable migration for MySQL 8 and MariaDB.
-- Select the application database before running this file.
INSERT IGNORE INTO `roles` (`name`, `description`) VALUES
  ('MODERATOR', 'Can view submitted courses and materials and approve or reject publication; cannot create or edit content');

-- MySQL does not support MariaDB's ADD COLUMN / CREATE INDEX IF NOT EXISTS.
SET @ocw_moderation_ddl = (SELECT IF(COUNT(*) = 0,
  'ALTER TABLE `courses` ADD COLUMN `review_status` VARCHAR(20) NOT NULL DEFAULT ''PENDING''', 'SELECT 1')
  FROM information_schema.COLUMNS WHERE TABLE_SCHEMA = DATABASE() AND TABLE_NAME = 'courses' AND COLUMN_NAME = 'review_status');
PREPARE ocw_moderation_stmt FROM @ocw_moderation_ddl;
EXECUTE ocw_moderation_stmt;
DEALLOCATE PREPARE ocw_moderation_stmt;

SET @ocw_moderation_ddl = (SELECT IF(COUNT(*) = 0,
  'ALTER TABLE `courses` ADD COLUMN `review_reason` TEXT NULL', 'SELECT 1')
  FROM information_schema.COLUMNS WHERE TABLE_SCHEMA = DATABASE() AND TABLE_NAME = 'courses' AND COLUMN_NAME = 'review_reason');
PREPARE ocw_moderation_stmt FROM @ocw_moderation_ddl;
EXECUTE ocw_moderation_stmt;
DEALLOCATE PREPARE ocw_moderation_stmt;

SET @ocw_moderation_ddl = (SELECT IF(COUNT(*) = 0,
  'ALTER TABLE `courses` ADD COLUMN `reviewed_by` BIGINT UNSIGNED NULL', 'SELECT 1')
  FROM information_schema.COLUMNS WHERE TABLE_SCHEMA = DATABASE() AND TABLE_NAME = 'courses' AND COLUMN_NAME = 'reviewed_by');
PREPARE ocw_moderation_stmt FROM @ocw_moderation_ddl;
EXECUTE ocw_moderation_stmt;
DEALLOCATE PREPARE ocw_moderation_stmt;

SET @ocw_moderation_ddl = (SELECT IF(COUNT(*) = 0,
  'ALTER TABLE `courses` ADD COLUMN `reviewed_at` DATETIME NULL', 'SELECT 1')
  FROM information_schema.COLUMNS WHERE TABLE_SCHEMA = DATABASE() AND TABLE_NAME = 'courses' AND COLUMN_NAME = 'reviewed_at');
PREPARE ocw_moderation_stmt FROM @ocw_moderation_ddl;
EXECUTE ocw_moderation_stmt;
DEALLOCATE PREPARE ocw_moderation_stmt;

SET @ocw_moderation_ddl = (SELECT IF(COUNT(*) = 0,
  'ALTER TABLE `courses` ADD COLUMN `review_version` INT NOT NULL DEFAULT 0', 'SELECT 1')
  FROM information_schema.COLUMNS WHERE TABLE_SCHEMA = DATABASE() AND TABLE_NAME = 'courses' AND COLUMN_NAME = 'review_version');
PREPARE ocw_moderation_stmt FROM @ocw_moderation_ddl;
EXECUTE ocw_moderation_stmt;
DEALLOCATE PREPARE ocw_moderation_stmt;

SET @ocw_moderation_ddl = (SELECT IF(COUNT(*) = 0,
  'CREATE INDEX `ix_courses_review_status` ON `courses` (`review_status`)', 'SELECT 1')
  FROM information_schema.STATISTICS WHERE TABLE_SCHEMA = DATABASE() AND TABLE_NAME = 'courses' AND INDEX_NAME = 'ix_courses_review_status');
PREPARE ocw_moderation_stmt FROM @ocw_moderation_ddl;
EXECUTE ocw_moderation_stmt;
DEALLOCATE PREPARE ocw_moderation_stmt;

SET @ocw_moderation_ddl = (SELECT IF(COUNT(*) = 0,
  'ALTER TABLE `courses` ADD CONSTRAINT `fk_courses_reviewer` FOREIGN KEY (`reviewed_by`) REFERENCES `users` (`id`) ON DELETE SET NULL', 'SELECT 1')
  FROM information_schema.KEY_COLUMN_USAGE WHERE TABLE_SCHEMA = DATABASE() AND TABLE_NAME = 'courses'
    AND COLUMN_NAME = 'reviewed_by' AND REFERENCED_TABLE_NAME = 'users' AND REFERENCED_COLUMN_NAME = 'id');
PREPARE ocw_moderation_stmt FROM @ocw_moderation_ddl;
EXECUTE ocw_moderation_stmt;
DEALLOCATE PREPARE ocw_moderation_stmt;

-- Existing published courses already passed the former admin publication workflow.
-- The version condition makes this safe to rerun without altering newer decisions.
UPDATE `courses` SET `review_status` = 'APPROVED', `updated_at` = `updated_at`
WHERE `status` = 'PUBLISHED' AND `review_status` = 'PENDING' AND `review_version` = 0;

CREATE TABLE IF NOT EXISTS `course_reviews` (
  `id` BIGINT UNSIGNED NOT NULL AUTO_INCREMENT,
  `course_id` BIGINT UNSIGNED NOT NULL,
  `reviewed_by` BIGINT UNSIGNED NULL,
  `status` VARCHAR(20) NOT NULL,
  `reason` TEXT NULL,
  `review_version` INT NOT NULL,
  `reviewed_at` DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
  PRIMARY KEY (`id`),
  UNIQUE KEY `uq_course_review_version` (`course_id`, `review_version`),
  KEY `ix_course_reviews_course_id` (`course_id`),
  CONSTRAINT `fk_course_reviews_course` FOREIGN KEY (`course_id`) REFERENCES `courses` (`id`) ON DELETE CASCADE,
  CONSTRAINT `fk_course_reviews_reviewer` FOREIGN KEY (`reviewed_by`) REFERENCES `users` (`id`) ON DELETE SET NULL
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;
