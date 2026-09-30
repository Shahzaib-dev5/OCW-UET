ALTER TABLE `courses`
    ADD COLUMN IF NOT EXISTS `category` VARCHAR(150) NULL AFTER `description`,
    ADD COLUMN IF NOT EXISTS `credit_hours` INT NULL AFTER `category`,
    ADD COLUMN IF NOT EXISTS `duration` VARCHAR(100) NULL AFTER `credit_hours`,
    ADD COLUMN IF NOT EXISTS `course_type` VARCHAR(100) NULL AFTER `duration`,
    ADD COLUMN IF NOT EXISTS `syllabus` TEXT NULL AFTER `course_type`;
