import enum

from app.extensions import db,BigIntegerUnsigned


class InternshipStatus(enum.Enum):
    DRAFT = "DRAFT"
    OPEN = "OPEN"
    CLOSED = "CLOSED"
    ARCHIVED = "ARCHIVED"


class Internship(db.Model):
    __tablename__ = "internships"

    id = db.Column(
        BigIntegerUnsigned,
        primary_key=True,
        autoincrement=True,
    )

    department_id = db.Column(
        BigIntegerUnsigned,
        db.ForeignKey(
            "departments.id",
            name="fk_internships_department",
            ondelete="CASCADE",
        ),
        nullable=False,
        index=True,
    )

    title = db.Column(
        db.String(255),
        nullable=False,
    )

    slug = db.Column(
        db.String(255),
        unique=True,
        nullable=False,
    )

    description = db.Column(
        db.Text,
        nullable=True,
    )

    category = db.Column(
        db.String(150),
        nullable=True,
    )

    duration = db.Column(
        db.String(100),
        nullable=True,
    )

    eligibility = db.Column(
        db.Text,
        nullable=True,
    )

    application_url = db.Column(
        db.String(1000),
        nullable=True,
    )

    thumbnail = db.Column(
        db.String(500),
        nullable=True,
    )

    start_date = db.Column(
        db.Date,
        nullable=True,
    )

    end_date = db.Column(
        db.Date,
        nullable=True,
    )

    status = db.Column(
        db.Enum(
            InternshipStatus,
            name="internship_status",
        ),
        default=InternshipStatus.DRAFT,
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

    department = db.relationship(
        "Department",
        back_populates="internships",
    )

    resources = db.relationship(
        "InternshipResource",
        back_populates="internship",
        cascade="all, delete-orphan",
        passive_deletes=True,
        order_by="InternshipResource.display_order",
    )

    def __repr__(self):
        return f"<Internship {self.title}>"
