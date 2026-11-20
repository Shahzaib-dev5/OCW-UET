ALTER TABLE course_resources
  ADD COLUMN department_id BIGINT UNSIGNED NULL AFTER course_id,
  ADD INDEX ix_course_resources_department_id (department_id),
  ADD CONSTRAINT fk_course_resources_department
    FOREIGN KEY (department_id) REFERENCES departments(id) ON DELETE CASCADE;
