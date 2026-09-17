from typing import Literal, NotRequired, TypedDict


ApplicationStatus = Literal["PENDING", "APPROVED", "REJECTED"]
RoleName = Literal["ADMIN", "TEACHER", "STUDENT"]


class RolePayload(TypedDict, total=False):
    name: RoleName
    description: str | None


class LoginPayload(TypedDict, total=False):
    email: str
    username: str
    password: str


class RegisterPayload(TypedDict):
    username: str
    email: str
    password: str
    role: NotRequired[RoleName]
    full_name: NotRequired[str | None]


class UserCreatePayload(RegisterPayload, total=False):
    role_id: int
    generate_password: bool


class CredentialResponse(TypedDict, total=False):
    status: str
    data: dict
    temporary_password: str


class CourseTeachingApplicationPayload(TypedDict):
    course_id: int
    message: NotRequired[str | None]


class CourseEnrollmentPayload(TypedDict):
    course_id: int
    message: NotRequired[str | None]


class ReviewPayload(TypedDict, total=False):
    status: ApplicationStatus
    message: str | None


class UploadResponse(TypedDict, total=False):
    status: str
    filename: str
    stored_name: str
    absolute_path: str
    relative_path: str
    local_url: str
    public_url: str
    media_id: int
