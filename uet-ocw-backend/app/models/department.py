import enum

from app.extensions import db,BigIntegerUnsigned


class DepartmentType(enum.Enum):
    DEPARTMENT = "DEPARTMENT"
    INSTITUTE = "INSTITUTE"
    CENTER = "CENTER"
    LAB = "LAB"
    OTHER = "OTHER"


class Department(db.Model):
    __tablename__ = "departments"

    id = db.Column(
        BigIntegerUnsigned,
        primary_key=True,
        autoincrement=True,
    )

    faculty_id = db.Column(
        BigIntegerUnsigned,
        db.ForeignKey(
            "faculties.id",
            name="fk_departments_faculty",
            ondelete="SET NULL",
        ),
        nullable=True,
        index=True,
    )

    name = db.Column(
        db.String(255),
        nullable=False,
    )

    short_name = db.Column(
        db.String(100),
        nullable=True,
    )

    department_type = db.Column(
        db.Enum(
            DepartmentType,
            name="department_type",
            native_enum=True,
        ),
        nullable=False,
        default=DepartmentType.DEPARTMENT,
        server_default="DEPARTMENT",
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
    faculty = db.relationship(
        "Faculty",
        back_populates="departments",
    )

    courses = db.relationship(
        "Course",
        back_populates="department",
        passive_deletes=True,
        lazy="dynamic",
    )

    internships = db.relationship(
        "Internship",
        back_populates="department",
        passive_deletes=True,
        lazy="dynamic",
    )

    research_papers = db.relationship(
        "ResearchPaper",
        back_populates="department",
        passive_deletes=True,
        lazy="dynamic",
    )

    def __repr__(self):
        return f"<Department {self.name}>"