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

    owner_id = db.Column(
        BigIntegerUnsigned,
        db.ForeignKey("users.id", name="fk_invited_talks_owner", ondelete="SET NULL"),
        nullable=True,
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

    review_status = db.Column(
        db.String(20), nullable=False, default="PENDING", server_default="PENDING", index=True
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
    owner = db.relationship("User", foreign_keys=[owner_id])
    resources = db.relationship(
        "InvitedTalkResource", back_populates="talk", cascade="all, delete-orphan",
        passive_deletes=True, order_by="InvitedTalkResource.display_order",
    )

    def __repr__(self):
        return f"<InvitedTalk {self.talk_title}>"


class InvitedTalkResource(db.Model):
    __tablename__ = "invited_talk_resources"

    id = db.Column(BigIntegerUnsigned, primary_key=True, autoincrement=True)
    talk_id = db.Column(
        BigIntegerUnsigned,
        db.ForeignKey("invited_talks.id", name="fk_invited_talk_resources_talk", ondelete="CASCADE"),
        nullable=False, index=True,
    )
    title = db.Column(db.String(255), nullable=False)
    resource_type = db.Column(db.String(30), nullable=False, default="LINK", server_default="LINK")
    url = db.Column(db.String(1000), nullable=False)
    description = db.Column(db.Text, nullable=True)
    display_order = db.Column(db.Integer, nullable=False, default=0, server_default="0")
    created_at = db.Column(db.DateTime, server_default=db.func.current_timestamp())
    updated_at = db.Column(db.DateTime, server_default=db.func.current_timestamp(), onupdate=db.func.current_timestamp())

    talk = db.relationship("InvitedTalk", back_populates="resources")
