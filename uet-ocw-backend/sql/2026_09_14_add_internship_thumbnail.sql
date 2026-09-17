ALTER TABLE `internships`
    ADD COLUMN IF NOT EXISTS `thumbnail` VARCHAR(500) NULL AFTER `application_url`;
