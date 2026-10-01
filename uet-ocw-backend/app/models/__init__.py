from app.models.author import Author
from app.models.course import Course
from app.models.department import Department
from app.models.enrollment import CourseEnrollment, CourseTeachingApplication
from app.models.faculty import Faculty
from app.models.internship import Internship
from app.models.internship_resource import InternshipResource
from app.models.invited_talk import InvitedTalk
from app.models.lecture import Lecture
from app.models.menu import MenuItem
from app.models.media import MediaFile
from app.models.research import ResearchPaper, ResearchPaperAuthor
from app.models.resource import CourseResource
from app.models.role import Role
from app.models.site_setting import SiteSetting
from app.models.user import User

__all__ = [
    "Author",
    "Course",
    "Department",
    "CourseEnrollment",
    "CourseTeachingApplication",
    "Faculty",
    "Internship",
    "InternshipResource",
    "InvitedTalk",
    "Lecture",
    "MenuItem",
    "MediaFile",
    "ResearchPaper",
    "ResearchPaperAuthor",
    "CourseResource",
    "Role",
    "SiteSetting",
    "User",
]
