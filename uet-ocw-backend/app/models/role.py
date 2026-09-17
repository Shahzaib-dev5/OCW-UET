from datetime import datetime

from app.extensions import db,BigIntegerUnsigned


class Role(db.Model):
    __tablename__ = "roles"

    id = db.Column(
        BigIntegerUnsigned,
        primary_key=True,
        autoincrement=True,
    )

    name = db.Column(
        db.String(50),
        unique=True,
        nullable=False,
        index=True,
    )

    description = db.Column(db.String(255))

    created_at = db.Column(
        db.DateTime,
        server_default=db.func.current_timestamp(),
        nullable=True,
    )

    # Relationship
    users = db.relationship(
        "User",
        back_populates="role",
        lazy="dynamic",
    )

    def __repr__(self):
        return f"<Role {self.name}>"
