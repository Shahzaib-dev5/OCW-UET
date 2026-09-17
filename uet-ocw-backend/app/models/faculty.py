from app.extensions import db,BigIntegerUnsigned


class Faculty(db.Model):
    __tablename__ = "faculties"

    id = db.Column(
        BigIntegerUnsigned,
        primary_key=True,
        autoincrement=True,
    )

    name = db.Column(
        db.String(255),
        nullable=False,
        unique=True,
    )

    short_name = db.Column(
        db.String(100),
        nullable=True,
    )

    description = db.Column(
        db.Text,
        nullable=True,
    )

    logo = db.Column(
        db.String(500),
        nullable=True,
    )

    website_url = db.Column(
        db.String(500),
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

    # Relationships
    departments = db.relationship(
        "Department",
        back_populates="faculty",
        passive_deletes=True,
        lazy="dynamic",
    )

    def __repr__(self):
        return f"<Faculty {self.name}>"