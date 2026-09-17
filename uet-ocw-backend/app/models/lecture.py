from app.extensions import db,BigIntegerUnsigned


class Lecture(db.Model):
    __tablename__ = "lectures"

    id = db.Column(
        BigIntegerUnsigned,
        primary_key=True,
        autoincrement=True,
    )

    course_id = db.Column(
        BigIntegerUnsigned,
        db.ForeignKey(
            "courses.id",
            name="fk_lectures_course",
            ondelete="CASCADE",
        ),
        nullable=False,
        index=True,
    )

    lecture_number = db.Column(
        db.Integer,
        nullable=False,
    )

    title = db.Column(
        db.String(255),
        nullable=False,
    )

    description = db.Column(
        db.Text,
        nullable=True,
    )

    duration_minutes = db.Column(
        db.Integer,
        nullable=True,
    )

    video_url = db.Column(
        db.String(1000),
        nullable=True,
    )

    presentation_url = db.Column(
        db.String(1000),
        nullable=True,
    )

    notes_url = db.Column(
        db.String(1000),
        nullable=True,
    )

    is_published = db.Column(
        db.Boolean,
        default=False,
        server_default="0",
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

    __table_args__ = (
        db.UniqueConstraint(
            "course_id",
            "lecture_number",
            name="uq_course_lecture",
        ),
    )

    course = db.relationship(
        "Course",
        back_populates="lectures",
    )

    def __repr__(self):
        return f"<Lecture {self.title}>"