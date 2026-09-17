from app.extensions import db, BigIntegerUnsigned


class MediaFile(db.Model):
    __tablename__ = "media_files"

    id = db.Column(
        BigIntegerUnsigned,
        primary_key=True,
        autoincrement=True,
    )

    original_name = db.Column(
        db.String(255),
        nullable=False,
    )

    stored_name = db.Column(
        db.String(255),
        nullable=True,
    )

    file_path = db.Column(
        db.String(1000),
        nullable=True,
    )

    file_url = db.Column(
        db.String(1000),
        nullable=True,
    )

    mime_type = db.Column(
        db.String(100),
        nullable=True,
        index=True,
    )

    file_size = db.Column(
        BigIntegerUnsigned,
        nullable=True,
    )

    uploaded_by = db.Column(
        BigIntegerUnsigned,
        db.ForeignKey(
            "users.id",
            name="fk_media_user",
            ondelete="SET NULL",
        ),
        nullable=True,
        index=True,
    )

    created_at = db.Column(
        db.DateTime,
        server_default=db.func.current_timestamp(),
    )

    uploader = db.relationship(
        "User",
        back_populates="media_files",
    )

    def __repr__(self):
        return f"<MediaFile {self.original_name}>"
