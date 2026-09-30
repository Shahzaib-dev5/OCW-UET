import enum

from app.extensions import db, BigIntegerUnsigned


class CourseLevel(enum.Enum):
    BEGINNER = "BEGINNER"
    INTERMEDIATE = "INTERMEDIATE"
    ADVANCED = "ADVANCED"
    UNDERGRADUATE = "UNDERGRADUATE"
    GRADUATE = "GRADUATE"
    OTHER = "OTHER"


class CourseStatus(enum.Enum):
    DRAFT = "DRAFT"
    PUBLISHED = "PUBLISHED"
    ARCHIVED = "ARCHIVED"


class Course(db.Model):
    __tablename__ = "courses"

    id = db.Column(
        BigIntegerUnsigned,
        primary_key=True,
        autoincrement=True,
    )

    department_id = db.Column(
        BigIntegerUnsigned,
        db.ForeignKey(
            "departments.id",
            name="fk_courses_department",
            ondelete="CASCADE",
        ),
        nullable=False,
        index=True,
    )

    course_code = db.Column(
        db.String(50),
        nullable=True,
    )

    title = db.Column(
        db.String(255),
        nullable=False,
    )

    slug = db.Column(
        db.String(255),
        nullable=False,
        unique=True,
        index=True,
    )

    short_description = db.Column(
        db.Text,
        nullable=True,
    )

    description = db.Column(
        db.Text().with_variant(db.Text, "mysql"),
        nullable=True,
    )

    category = db.Column(
        db.String(150),
        nullable=True,
    )

    credit_hours = db.Column(
        db.Integer,
        nullable=True,
    )

    duration = db.Column(
        db.String(100),
        nullable=True,
    )

    course_type = db.Column(
        db.String(100),
        nullable=True,
    )

    syllabus = db.Column(
        db.Text().with_variant(db.Text, "mysql"),
        nullable=True,
    )

    instructor_name = db.Column(
        db.String(255),
        nullable=True,
    )

    instructor_email = db.Column(
        db.String(150),
        nullable=True,
    )

    level = db.Column(
        db.Enum(
            CourseLevel,
            name="course_level",
        ),
        nullable=True,
        default=CourseLevel.UNDERGRADUATE,
        server_default="UNDERGRADUATE",
    )

    semester = db.Column(
        db.String(50),
        nullable=True,
    )

    academic_year = db.Column(
        db.String(20),
        nullable=True,
    )

    thumbnail = db.Column(
        db.String(500),
        nullable=True,
    )

    status = db.Column(
        db.Enum(
            CourseStatus,
            name="course_status",
        ),
        nullable=True,
        default=CourseStatus.DRAFT,
        server_default="DRAFT",
        index=True,
    )

    display_order = db.Column(
        db.Integer,
        default=0,
        server_default="0",
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
    department = db.relationship(
        "Department",
        back_populates="courses",
    )

    lectures = db.relationship(
        "Lecture",
        back_populates="course",
        cascade="all, delete-orphan",
        passive_deletes=True,
        order_by="Lecture.display_order",
    )

    resources = db.relationship(
        "CourseResource",
        back_populates="course",
        cascade="all, delete-orphan",
        passive_deletes=True,
        order_by="CourseResource.display_order",
    )

    teaching_applications = db.relationship(
        "CourseTeachingApplication",
        back_populates="course",
        cascade="all, delete-orphan",
        passive_deletes=True,
    )

    course_enrollments = db.relationship(
        "CourseEnrollment",
        back_populates="course",
        cascade="all, delete-orphan",
        passive_deletes=True,
    )

    def __repr__(self):
        return f"<Course {self.title}>"
