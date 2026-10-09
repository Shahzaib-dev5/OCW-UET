-- Data-preserving migration for student auth, public/restricted access,
-- generic enrollment requests, instructor applications, and course ownership.

ALTER TABLE users
  ADD COLUMN auth_provider VARCHAR(30) NOT NULL DEFAULT 'password',
  ADD COLUMN google_sub VARCHAR(255) NULL,
  ADD COLUMN email_verified TINYINT(1) NOT NULL DEFAULT 0,
  ADD COLUMN reset_token_hash VARCHAR(255) NULL,
  ADD COLUMN reset_token_expires_at DATETIME NULL,
  ADD COLUMN instructor_status VARCHAR(30) NOT NULL DEFAULT 'NONE',
  ADD UNIQUE KEY uq_users_google_sub (google_sub),
  ADD KEY ix_users_instructor_status (instructor_status);

ALTER TABLE courses
  ADD COLUMN owner_id BIGINT UNSIGNED NULL,
  ADD COLUMN learning_outcomes TEXT NULL,
  ADD COLUMN schedule TEXT NULL,
  ADD COLUMN access_level ENUM('PUBLIC','RESTRICTED') NOT NULL DEFAULT 'PUBLIC',
  ADD KEY ix_courses_owner_id (owner_id),
  ADD KEY ix_courses_access_level (access_level),
  ADD CONSTRAINT fk_courses_owner FOREIGN KEY (owner_id) REFERENCES users(id) ON DELETE SET NULL;

ALTER TABLE course_resources
  ADD COLUMN access_level ENUM('PUBLIC','RESTRICTED') NOT NULL DEFAULT 'PUBLIC',
  ADD KEY ix_course_resources_access_level (access_level);

ALTER TABLE internships
  ADD COLUMN schedule TEXT NULL,
  ADD COLUMN access_level ENUM('PUBLIC','RESTRICTED') NOT NULL DEFAULT 'PUBLIC',
  ADD KEY ix_internships_access_level (access_level);

ALTER TABLE course_enrollments
  MODIFY COLUMN status ENUM('PENDING','APPROVED','REJECTED','REVOKED') NOT NULL DEFAULT 'PENDING',
  ADD COLUMN review_reason TEXT NULL;

ALTER TABLE course_teaching_applications
  MODIFY COLUMN status ENUM('PENDING','APPROVED','REJECTED','REVOKED') NOT NULL DEFAULT 'PENDING',
  ADD COLUMN review_reason TEXT NULL;

CREATE TABLE IF NOT EXISTS resource_enrollments (
  id BIGINT UNSIGNED NOT NULL AUTO_INCREMENT,
  student_id BIGINT UNSIGNED NOT NULL,
  resource_type ENUM('COURSE','BOOK','SKILL') NOT NULL,
  resource_id BIGINT UNSIGNED NOT NULL,
  status ENUM('PENDING','APPROVED','REJECTED','REVOKED') NOT NULL DEFAULT 'PENDING',
  message TEXT NULL,
  review_reason TEXT NULL,
  reviewed_by BIGINT UNSIGNED NULL,
  reviewed_at DATETIME NULL,
  created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
  updated_at DATETIME DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
  PRIMARY KEY (id),
  KEY ix_resource_enrollments_student_id (student_id),
  KEY ix_resource_enrollments_resource (resource_type, resource_id),
  KEY ix_resource_enrollments_status (status),
  KEY ix_resource_enrollments_reviewed_by (reviewed_by),
  CONSTRAINT fk_resource_enrollments_student FOREIGN KEY (student_id) REFERENCES users(id) ON DELETE CASCADE,
  CONSTRAINT fk_resource_enrollments_reviewer FOREIGN KEY (reviewed_by) REFERENCES users(id) ON DELETE SET NULL
);

CREATE TABLE IF NOT EXISTS instructor_applications (
  id BIGINT UNSIGNED NOT NULL AUTO_INCREMENT,
  user_id BIGINT UNSIGNED NOT NULL,
  status ENUM('PENDING','APPROVED','REJECTED','REVOKED') NOT NULL DEFAULT 'PENDING',
  qualifications TEXT NULL,
  expertise TEXT NULL,
  teaching_bio TEXT NULL,
  contact_details TEXT NULL,
  affiliation VARCHAR(255) NULL,
  review_reason TEXT NULL,
  reviewed_by BIGINT UNSIGNED NULL,
  reviewed_at DATETIME NULL,
  created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
  updated_at DATETIME DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
  PRIMARY KEY (id),
  KEY ix_instructor_applications_user_id (user_id),
  KEY ix_instructor_applications_status (status),
  KEY ix_instructor_applications_reviewed_by (reviewed_by),
  CONSTRAINT fk_instructor_applications_user FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE,
  CONSTRAINT fk_instructor_applications_reviewer FOREIGN KEY (reviewed_by) REFERENCES users(id) ON DELETE SET NULL
);
