from app.extensions import db,BigIntegerUnsigned


class User(db.Model):
    __tablename__ = "users"

    id = db.Column(
       BigIntegerUnsigned,
        primary_key=True,
        autoincrement=True,
    )

    role_id = db.Column(
        BigIntegerUnsigned,
        db.ForeignKey(
            "roles.id",
            name="fk_users_role",
        ),
        nullable=False,
        index=True,
    )

    username = db.Column(
        db.String(100),
        unique=True,
        nullable=False,
    )

    email = db.Column(
        db.String(150),
        unique=True,
        nullable=False,
    )

    password_hash = db.Column(
        db.String(255),
        nullable=False,
    )

    full_name = db.Column(
        db.String(150),
        nullable=True,
    )

    is_active = db.Column(
        db.Boolean,
        default=True,
        server_default="1",
    )

    last_login = db.Column(
        db.DateTime,
        nullable=True,
    )

    created_at = db.Column(
        db.DateTime,
        server_default=db.func.current_timestamp(),
    )

    updated_at = db.Column(
        db.DateTime,
        server_default=db.func.current_timestamp(),
        onupdate=db.func.current_timestamp(),
    )

    # Relationships
    role = db.relationship(
        "Role",
        back_populates="users",
    )

    media_files = db.relationship(
        "MediaFile",
        back_populates="uploader",
        passive_deletes=True,
    )

    teaching_applications = db.relationship(
        "CourseTeachingApplication",
        foreign_keys="CourseTeachingApplication.teacher_id",
        back_populates="teacher",
        cascade="all, delete-orphan",
        passive_deletes=True,
    )

    course_enrollments = db.relationship(
        "CourseEnrollment",
        foreign_keys="CourseEnrollment.student_id",
        back_populates="student",
        cascade="all, delete-orphan",
        passive_deletes=True,
    )

    def __repr__(self):
        return f"<User {self.username}>"
