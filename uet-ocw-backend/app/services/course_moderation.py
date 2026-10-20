from sqlalchemy import update

from app.extensions import db
from app.models.course import Course, CourseStatus
from app.services.authz import current_user, is_admin


def course_content_changed(course_id):
    """Invalidate outstanding previews in the same transaction as a content edit."""
    if not course_id:
        return
    values = {"review_version": Course.review_version + 1}
    if not is_admin(current_user()):
        values.update(
            status=CourseStatus.DRAFT,
            review_status="PENDING",
            review_reason=None,
            reviewed_by=None,
            reviewed_at=None,
        )
    course = db.session.get(Course, course_id)
    db.session.execute(update(Course).where(Course.id == course_id).values(**values),
                       execution_options={"synchronize_session": False})
    if course is not None:
        # A decision may have committed since this request first read the course.
        # Reload the database's incremented version instead of incrementing a stale
        # in-memory value when a legacy admin publish also writes an audit record.
        db.session.expire(course, ["status", "review_status", "review_reason", "reviewed_by",
                                  "reviewed_at", "review_version", "updated_at", "reviewer"])
