from sqlalchemy.exc import SQLAlchemyError

from app.extensions import db
from app.models.enrollment import CourseEnrollment, CourseTeachingApplication


def ensure_rbac_tables():
    try:
        CourseTeachingApplication.__table__.create(db.engine, checkfirst=True)
        CourseEnrollment.__table__.create(db.engine, checkfirst=True)
    except SQLAlchemyError:
        db.session.rollback()
        raise
