import enum

from app.extensions import db, BigIntegerUnsigned


class InvitedTalkStatus(enum.Enum):
    DRAFT = "DRAFT"
    PUBLISHED = "PUBLISHED"
    ARCHIVED = "ARCHIVED"


class InvitedTalk(db.Model):
    __tablename__ = "invited_talks"

    id = db.Column(
        BigIntegerUnsigned,
        primary_key=True,
        autoincrement=True,
    )

    department_id = db.Column(
        BigIntegerUnsigned,
        db.ForeignKey(
            "departments.id",
            name="fk_invited_talks_department",
            ondelete="CASCADE",
        ),
        nullable=False,
        index=True,
    )

    talk_title = db.Column(
        db.String(500),
        nullable=False,
    )

    event_title = db.Column(
        db.String(500),
        nullable=True,
    )

    presenter = db.Column(
        db.String(255),
        nullable=True,
    )

    talk_date = db.Column(
        db.Date,
        nullable=True,
        index=True,
    )

    video_url = db.Column(
        db.String(1000),
        nullable=True,
    )

    upload_url = db.Column(
        db.String(1000),
        nullable=True,
    )

    publication = db.Column(
        db.String(1000),
        nullable=True,
    )

    status = db.Column(
        db.Enum(
            InvitedTalkStatus,
            name="invited_talk_status",
        ),
        default=InvitedTalkStatus.PUBLISHED,
        server_default="PUBLISHED",
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
        back_populates="invited_talks",
    )

    def __repr__(self):
        return f"<InvitedTalk {self.talk_title}>"
