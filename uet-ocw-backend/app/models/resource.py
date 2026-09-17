import enum

from app.extensions import db,BigIntegerUnsigned


class CourseResourceType(enum.Enum):
    PDF = "PDF"
    POWERPOINT = "POWERPOINT"
    VIDEO = "VIDEO"
    BOOK = "BOOK"
    DOCUMENT = "DOCUMENT"
    LINK = "LINK"
    AUDIO = "AUDIO"
    OTHER = "OTHER"


class CourseResource(db.Model):
    __tablename__ = "course_resources"

    id = db.Column(
        BigIntegerUnsigned,
        primary_key=True,
        autoincrement=True,
    )

    course_id = db.Column(
        BigIntegerUnsigned,
        db.ForeignKey(
            "courses.id",
            name="fk_course_resources_course",
            ondelete="CASCADE",
        ),
        nullable=False,
        index=True,
    )

    title = db.Column(
        db.String(255),
        nullable=False,
    )

    resource_type = db.Column(
        db.Enum(
            CourseResourceType,
            name="course_resource_type",
        ),
        nullable=False,
        index=True,
    )

    description = db.Column(
        db.Text,
        nullable=True,
    )

    file_url = db.Column(
        db.String(1000),
        nullable=True,
    )

    external_url = db.Column(
        db.String(1000),
        nullable=True,
    )

    file_size = db.Column(
        BigIntegerUnsigned,
        nullable=True,
    )

    mime_type = db.Column(
        db.String(100),
        nullable=True,
    )

    lecture_number = db.Column(
        db.Integer,
        nullable=True,
    )

    display_order = db.Column(
        db.Integer,
        default=0,
        server_default="0",
    )

    is_active = db.Column(
        db.Boolean,
        default=True,
        server_default="1",
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

    course = db.relationship(
        "Course",
        back_populates="resources",
    )

    def __repr__(self):
        return f"<CourseResource {self.title}>"