ALTER TABLE courses
  ADD COLUMN login_required TINYINT(1) NOT NULL DEFAULT 0,
  ADD KEY ix_courses_login_required (login_required);
