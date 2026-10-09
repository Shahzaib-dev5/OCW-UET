-- Adds student profile fields and OTP verification state for secure signup.

ALTER TABLE users
  ADD COLUMN email_otp_hash VARCHAR(255) NULL,
  ADD COLUMN email_otp_expires_at DATETIME NULL,
  ADD COLUMN email_otp_attempts INT NOT NULL DEFAULT 0,
  ADD COLUMN date_of_birth DATE NULL,
  ADD COLUMN cnic VARCHAR(20) NULL,
  ADD COLUMN gender VARCHAR(30) NULL,
  ADD COLUMN university_name VARCHAR(255) NULL,
  ADD COLUMN department_name VARCHAR(255) NULL,
  ADD COLUMN academic_status VARCHAR(30) NULL,
  ADD COLUMN semester VARCHAR(50) NULL,
  ADD UNIQUE KEY uq_users_cnic (cnic);
