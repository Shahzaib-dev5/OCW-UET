ALTER TABLE course_resources
  MODIFY COLUMN course_id BIGINT UNSIGNED NULL,
  ADD COLUMN thumbnail VARCHAR(500) NULL AFTER external_url,
  ADD COLUMN owner_id BIGINT UNSIGNED NULL AFTER course_id,
  ADD KEY ix_course_resources_owner_id (owner_id),
  ADD CONSTRAINT fk_course_resources_owner FOREIGN KEY (owner_id) REFERENCES users(id) ON DELETE SET NULL;

UPDATE course_resources cr
JOIN courses c ON c.id = cr.course_id
SET cr.owner_id = c.owner_id
WHERE cr.resource_type = 'BOOK'
  AND cr.owner_id IS NULL
  AND c.owner_id IS NOT NULL;
