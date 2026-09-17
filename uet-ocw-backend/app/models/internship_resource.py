import enum

from app.extensions import db,BigIntegerUnsigned


class InternshipResourceType(enum.Enum):
    PDF = "PDF"
    DOCUMENT = "DOCUMENT"
    VIDEO = "VIDEO"
    LINK = "LINK"
    IMAGE = "IMAGE"
    OTHER = "OTHER"


class InternshipResource(db.Model):
    __tablename__ = "internship_resources"

    id = db.Column(
        BigIntegerUnsigned,
        primary_key=True,
        autoincrement=True,
    )

    internship_id = db.Column(
        BigIntegerUnsigned,
        db.ForeignKey(
            "internships.id",
            name="fk_internship_resources",
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
            InternshipResourceType,
            name="internship_resource_type",
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

    internship = db.relationship(
        "Internship",
        back_populates="resources",
    )

    def __repr__(self):
        return f"<InternshipResource {self.title}>"
