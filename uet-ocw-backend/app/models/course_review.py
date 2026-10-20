from app.extensions import BigIntegerUnsigned, db


class CourseReview(db.Model):
    """An append-only record of a course publication decision."""

    __tablename__ = "course_reviews"

    id = db.Column(BigIntegerUnsigned, primary_key=True, autoincrement=True)
    course_id = db.Column(BigIntegerUnsigned, db.ForeignKey("courses.id", ondelete="CASCADE"), nullable=False, index=True)
    reviewed_by = db.Column(BigIntegerUnsigned, db.ForeignKey("users.id", ondelete="SET NULL"), nullable=True)
    status = db.Column(db.String(20), nullable=False)
    reason = db.Column(db.Text, nullable=True)
    review_version = db.Column(db.Integer, nullable=False)
    reviewed_at = db.Column(db.DateTime, nullable=False, server_default=db.func.current_timestamp())

    reviewer = db.relationship("User", foreign_keys=[reviewed_by])

    __table_args__ = (db.UniqueConstraint("course_id", "review_version", name="uq_course_review_version"),)
