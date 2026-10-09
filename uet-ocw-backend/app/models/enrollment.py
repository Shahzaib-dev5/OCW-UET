import enum

from app.extensions import BigIntegerUnsigned, db


class ApplicationStatus(enum.Enum):
    PENDING = "PENDING"
    APPROVED = "APPROVED"
    REJECTED = "REJECTED"
    REVOKED = "REVOKED"


class ResourceType(enum.Enum):
    COURSE = "COURSE"
    BOOK = "BOOK"
    SKILL = "SKILL"


class CourseTeachingApplication(db.Model):
    __tablename__ = "course_teaching_applications"

    id = db.Column(BigIntegerUnsigned, primary_key=True, autoincrement=True)
    teacher_id = db.Column(
        BigIntegerUnsigned,
        db.ForeignKey("users.id", name="fk_course_teaching_teacher", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    course_id = db.Column(
        BigIntegerUnsigned,
        db.ForeignKey("courses.id", name="fk_course_teaching_course", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    status = db.Column(
        db.Enum(ApplicationStatus, name="course_teaching_application_status"),
        nullable=False,
        default=ApplicationStatus.PENDING,
        server_default="PENDING",
        index=True,
    )
    message = db.Column(db.Text, nullable=True)
    review_reason = db.Column(db.Text, nullable=True)
    reviewed_by = db.Column(
        BigIntegerUnsigned,
        db.ForeignKey("users.id", name="fk_course_teaching_reviewer", ondelete="SET NULL"),
        nullable=True,
        index=True,
    )
    reviewed_at = db.Column(db.DateTime, nullable=True)
    created_at = db.Column(db.DateTime, server_default=db.func.current_timestamp())
    updated_at = db.Column(
        db.DateTime,
        server_default=db.func.current_timestamp(),
        onupdate=db.func.current_timestamp(),
    )

    __table_args__ = (
        db.UniqueConstraint("teacher_id", "course_id", name="uq_teacher_course_application"),
    )

    teacher = db.relationship(
        "User",
        foreign_keys=[teacher_id],
        back_populates="teaching_applications",
    )
    reviewer = db.relationship("User", foreign_keys=[reviewed_by])
    course = db.relationship("Course", back_populates="teaching_applications")

    def __repr__(self):
        return f"<CourseTeachingApplication teacher={self.teacher_id} course={self.course_id}>"


class CourseEnrollment(db.Model):
    __tablename__ = "course_enrollments"

    id = db.Column(BigIntegerUnsigned, primary_key=True, autoincrement=True)
    student_id = db.Column(
        BigIntegerUnsigned,
        db.ForeignKey("users.id", name="fk_course_enrollments_student", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    course_id = db.Column(
        BigIntegerUnsigned,
        db.ForeignKey("courses.id", name="fk_course_enrollments_course", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    status = db.Column(
        db.Enum(ApplicationStatus, name="course_enrollment_status"),
        nullable=False,
        default=ApplicationStatus.PENDING,
        server_default="PENDING",
        index=True,
    )
    message = db.Column(db.Text, nullable=True)
    review_reason = db.Column(db.Text, nullable=True)
    reviewed_by = db.Column(
        BigIntegerUnsigned,
        db.ForeignKey("users.id", name="fk_course_enrollments_reviewer", ondelete="SET NULL"),
        nullable=True,
        index=True,
    )
    reviewed_at = db.Column(db.DateTime, nullable=True)
    created_at = db.Column(db.DateTime, server_default=db.func.current_timestamp())
    updated_at = db.Column(
        db.DateTime,
        server_default=db.func.current_timestamp(),
        onupdate=db.func.current_timestamp(),
    )

    __table_args__ = (
        db.UniqueConstraint("student_id", "course_id", name="uq_student_course_enrollment"),
    )

    student = db.relationship(
        "User",
        foreign_keys=[student_id],
        back_populates="course_enrollments",
    )
    reviewer = db.relationship("User", foreign_keys=[reviewed_by])
    course = db.relationship("Course", back_populates="course_enrollments")

    def __repr__(self):
        return f"<CourseEnrollment student={self.student_id} course={self.course_id}>"


class ResourceEnrollment(db.Model):
    __tablename__ = "resource_enrollments"

    id = db.Column(BigIntegerUnsigned, primary_key=True, autoincrement=True)
    student_id = db.Column(
        BigIntegerUnsigned,
        db.ForeignKey("users.id", name="fk_resource_enrollments_student", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    resource_type = db.Column(
        db.Enum(ResourceType, name="resource_enrollment_type"),
        nullable=False,
        index=True,
    )
    resource_id = db.Column(BigIntegerUnsigned, nullable=False, index=True)
    status = db.Column(
        db.Enum(ApplicationStatus, name="resource_enrollment_status"),
        nullable=False,
        default=ApplicationStatus.PENDING,
        server_default="PENDING",
        index=True,
    )
    message = db.Column(db.Text, nullable=True)
    review_reason = db.Column(db.Text, nullable=True)
    reviewed_by = db.Column(
        BigIntegerUnsigned,
        db.ForeignKey("users.id", name="fk_resource_enrollments_reviewer", ondelete="SET NULL"),
        nullable=True,
        index=True,
    )
    reviewed_at = db.Column(db.DateTime, nullable=True)
    created_at = db.Column(db.DateTime, server_default=db.func.current_timestamp())
    updated_at = db.Column(
        db.DateTime,
        server_default=db.func.current_timestamp(),
        onupdate=db.func.current_timestamp(),
    )

    student = db.relationship("User", foreign_keys=[student_id])
    reviewer = db.relationship("User", foreign_keys=[reviewed_by])

    def __repr__(self):
        return f"<ResourceEnrollment student={self.student_id} {self.resource_type}={self.resource_id}>"


class InstructorApplication(db.Model):
    __tablename__ = "instructor_applications"

    id = db.Column(BigIntegerUnsigned, primary_key=True, autoincrement=True)
    user_id = db.Column(
        BigIntegerUnsigned,
        db.ForeignKey("users.id", name="fk_instructor_applications_user", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    status = db.Column(
        db.Enum(ApplicationStatus, name="instructor_application_status"),
        nullable=False,
        default=ApplicationStatus.PENDING,
        server_default="PENDING",
        index=True,
    )
    qualifications = db.Column(db.Text, nullable=True)
    expertise = db.Column(db.Text, nullable=True)
    teaching_bio = db.Column(db.Text, nullable=True)
    contact_details = db.Column(db.Text, nullable=True)
    affiliation = db.Column(db.String(255), nullable=True)
    review_reason = db.Column(db.Text, nullable=True)
    reviewed_by = db.Column(
        BigIntegerUnsigned,
        db.ForeignKey("users.id", name="fk_instructor_applications_reviewer", ondelete="SET NULL"),
        nullable=True,
        index=True,
    )
    reviewed_at = db.Column(db.DateTime, nullable=True)
    created_at = db.Column(db.DateTime, server_default=db.func.current_timestamp())
    updated_at = db.Column(
        db.DateTime,
        server_default=db.func.current_timestamp(),
        onupdate=db.func.current_timestamp(),
    )

    user = db.relationship("User", foreign_keys=[user_id], back_populates="instructor_applications")
    reviewer = db.relationship("User", foreign_keys=[reviewed_by])

    def __repr__(self):
        return f"<InstructorApplication user={self.user_id} status={self.status}>"
