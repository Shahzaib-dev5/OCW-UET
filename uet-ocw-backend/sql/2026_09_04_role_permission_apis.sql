INSERT IGNORE INTO `roles` (`name`, `description`) VALUES
  ('ADMIN', 'Full access to all OCW management APIs'),
  ('TEACHER', 'Can apply to teach courses and manage resources for approved courses'),
  ('STUDENT', 'Can apply for courses and view resources after approval');

CREATE TABLE IF NOT EXISTS `course_teaching_applications` (
  `id` BIGINT UNSIGNED NOT NULL AUTO_INCREMENT,
  `teacher_id` BIGINT UNSIGNED NOT NULL,
  `course_id` BIGINT UNSIGNED NOT NULL,
  `status` ENUM('PENDING', 'APPROVED', 'REJECTED') NOT NULL DEFAULT 'PENDING',
  `message` TEXT NULL,
  `reviewed_by` BIGINT UNSIGNED NULL,
  `reviewed_at` DATETIME NULL,
  `created_at` DATETIME NULL DEFAULT CURRENT_TIMESTAMP,
  `updated_at` DATETIME NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
  PRIMARY KEY (`id`),
  UNIQUE KEY `uq_teacher_course_application` (`teacher_id`, `course_id`),
  KEY `ix_course_teaching_applications_teacher_id` (`teacher_id`),
  KEY `ix_course_teaching_applications_course_id` (`course_id`),
  KEY `ix_course_teaching_applications_status` (`status`),
  KEY `ix_course_teaching_applications_reviewed_by` (`reviewed_by`),
  CONSTRAINT `fk_course_teaching_teacher`
    FOREIGN KEY (`teacher_id`) REFERENCES `users` (`id`) ON DELETE CASCADE,
  CONSTRAINT `fk_course_teaching_course`
    FOREIGN KEY (`course_id`) REFERENCES `courses` (`id`) ON DELETE CASCADE,
  CONSTRAINT `fk_course_teaching_reviewer`
    FOREIGN KEY (`reviewed_by`) REFERENCES `users` (`id`) ON DELETE SET NULL
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

CREATE TABLE IF NOT EXISTS `course_enrollments` (
  `id` BIGINT UNSIGNED NOT NULL AUTO_INCREMENT,
  `student_id` BIGINT UNSIGNED NOT NULL,
  `course_id` BIGINT UNSIGNED NOT NULL,
  `status` ENUM('PENDING', 'APPROVED', 'REJECTED') NOT NULL DEFAULT 'PENDING',
  `message` TEXT NULL,
  `reviewed_by` BIGINT UNSIGNED NULL,
  `reviewed_at` DATETIME NULL,
  `created_at` DATETIME NULL DEFAULT CURRENT_TIMESTAMP,
  `updated_at` DATETIME NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
  PRIMARY KEY (`id`),
  UNIQUE KEY `uq_student_course_enrollment` (`student_id`, `course_id`),
  KEY `ix_course_enrollments_student_id` (`student_id`),
  KEY `ix_course_enrollments_course_id` (`course_id`),
  KEY `ix_course_enrollments_status` (`status`),
  KEY `ix_course_enrollments_reviewed_by` (`reviewed_by`),
  CONSTRAINT `fk_course_enrollments_student`
    FOREIGN KEY (`student_id`) REFERENCES `users` (`id`) ON DELETE CASCADE,
  CONSTRAINT `fk_course_enrollments_course`
    FOREIGN KEY (`course_id`) REFERENCES `courses` (`id`) ON DELETE CASCADE,
  CONSTRAINT `fk_course_enrollments_reviewer`
    FOREIGN KEY (`reviewed_by`) REFERENCES `users` (`id`) ON DELETE SET NULL
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;
