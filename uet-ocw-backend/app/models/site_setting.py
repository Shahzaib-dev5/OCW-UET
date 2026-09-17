from app.extensions import db,BigIntegerUnsigned


class SiteSetting(db.Model):
    __tablename__ = "site_settings"

    id = db.Column(
        BigIntegerUnsigned,
        primary_key=True,
        autoincrement=True,
    )

    setting_key = db.Column(
        db.String(100),
        nullable=False,
        unique=True,
    )

    setting_value = db.Column(
        db.Text,
        nullable=True,
    )

    setting_type = db.Column(
        db.String(50),
        default="TEXT",
        server_default="TEXT",
    )

    updated_at = db.Column(
        db.DateTime,
        server_default=db.func.current_timestamp(),
        onupdate=db.func.current_timestamp(),
    )

    def __repr__(self):
        return f"<SiteSetting {self.setting_key}>"