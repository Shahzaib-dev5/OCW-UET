# Complete Relationship APIs Documentation

This document provides a comprehensive list of all relationship-based APIs in the UET OCW Backend system.

---

## 1. **Research Paper - Author Linking** (`research_paper_authors`)

**Purpose**: Link research papers to their authors with ordering information

**Junction Table**: `research_paper_authors` (composite primary key)

**Endpoints**:
- `GET /api/research-authors` - List all author-paper relationships
- `GET /api/research-authors/paper/{research_paper_id}` - Get all authors for a specific research paper
- `GET /api/research-authors/author/{author_id}` - Get all papers by a specific author
- `POST /api/research-authors` - Create a new author-paper relationship
- `DELETE /api/research-authors/paper/{research_paper_id}/author/{author_id}` - Remove an author from a paper

**Example POST/PUT Payload**:
```json
{
  "research_paper_id": 1,
  "author_id": 2,
  "author_order": 1
}
```

**Status**: ✅ Complete with full CRUD

---

## 2. **Course - Lecture Linking** (`lectures`)

**Purpose**: Link lectures to courses with full lecture metadata

**Relationship Table**: `lectures` (with `course_id` foreign key)

**Endpoints**:
- `GET /api/lectures` - List all lectures
- `GET /api/lectures/course/{course_id}` - Get all lectures for a specific course
- `GET /api/lectures/{lecture_id}` - Get a specific lecture
- `POST /api/lectures` - Create a new lecture
- `PUT /api/lectures/{lecture_id}` - Update a lecture
- `PATCH /api/lectures/{lecture_id}` - Partially update a lecture
- `DELETE /api/lectures/{lecture_id}` - Delete a lecture

**Example POST/PUT Payload**:
```json
{
  "course_id": 1,
  "lecture_number": 1,
  "title": "Introduction to Python",
  "description": "Overview of variables and loops",
  "duration_minutes": 45,
  "video_url": "/uploads/video.mp4",
  "presentation_url": "/uploads/slides.pdf",
  "notes_url": "/uploads/notes.md",
  "is_published": true,
  "display_order": 1
}
```

**Status**: ✅ Complete with full CRUD

---

## 3. **Course - Resource Linking** (`course_resources`)

**Purpose**: Link course materials and resources to courses

**Relationship Table**: `course_resources` (with `course_id` foreign key)

**Endpoints**:
- `GET /api/course-resources` - List all course resources
- `GET /api/course-resources/course/{course_id}` - Get all resources for a specific course
- `GET /api/course-resources/{resource_id}` - Get a specific course resource
- `POST /api/course-resources` - Create a new course resource
- `PUT /api/course-resources/{resource_id}` - Update a course resource
- `PATCH /api/course-resources/{resource_id}` - Partially update a course resource
- `DELETE /api/course-resources/{resource_id}` - Delete a course resource

**Example POST/PUT Payload**:
```json
{
  "course_id": 1,
  "title": "Week 1 Lecture PDF",
  "resource_type": "pdf",
  "description": "Lecture material",
  "file_url": "/uploads/course.pdf",
  "external_url": "https://example.com/resource",
  "file_size": 120000,
  "mime_type": "application/pdf",
  "lecture_number": 1,
  "display_order": 1,
  "is_active": true
}
```

**Status**: ✅ Complete with full CRUD

---

## 4. **Internship - Resource Linking** (`internship_resources`)

**Purpose**: Link internship materials and guidelines to internship postings

**Relationship Table**: `internship_resources` (with `internship_id` foreign key)

**Endpoints**:
- `GET /api/internship-resources` - List all internship resources
- `GET /api/internship-resources/internship/{internship_id}` - Get all resources for a specific internship
- `GET /api/internship-resources/{resource_id}` - Get a specific internship resource
- `POST /api/internship-resources` - Create a new internship resource
- `PUT /api/internship-resources/{resource_id}` - Update an internship resource
- `PATCH /api/internship-resources/{resource_id}` - Partially update an internship resource
- `DELETE /api/internship-resources/{resource_id}` - Delete an internship resource

**Example POST/PUT Payload**:
```json
{
  "internship_id": 1,
  "title": "Application Guide",
  "resource_type": "PDF",
  "file_url": "/uploads/internship.pdf",
  "external_url": "https://example.com/guidelines",
  "display_order": 1
}
```

**Status**: ✅ Complete with full CRUD

---

## 5. **Menu Items - Hierarchical Relationships** (`menu_items`)

**Purpose**: Create hierarchical menu structures with parent-child relationships

**Relationship Table**: `menu_items` (self-referencing with `parent_id` foreign key)

**Endpoints**:
- `GET /api/menu` - List all menu items
- `GET /api/menu/{menu_id}` - Get a specific menu item with children
- `POST /api/menu` - Create a new menu item
- `PUT /api/menu/{menu_id}` - Update a menu item
- `PATCH /api/menu/{menu_id}` - Partially update a menu item
- `DELETE /api/menu/{menu_id}` - Delete a menu item (cascades to children)

**Example POST/PUT Payload**:
```json
{
  "parent_id": null,
  "title": "Home",
  "slug": "home",
  "url": "/",
  "menu_location": "HEADER",
  "icon": "home",
  "display_order": 1,
  "is_active": true
}
```

**Menu Locations**: `HEADER`, `FOOTER`, `SIDEBAR`

**Status**: ✅ Complete with full CRUD and hierarchical support

---

## 6. **Media Files - Upload Tracking** (`media_files`)

**Purpose**: Track uploaded files and metadata, linked to uploading users

**Relationship Table**: `media_files` (with `uploaded_by` foreign key to `users`)

**Endpoints**:
- `GET /api/media` - List all media files
- `GET /api/media/{media_id}` - Get a specific media file
- `POST /api/media` - Create/register a new media file record
- `PUT /api/media/{media_id}` - Update media file metadata
- `PATCH /api/media/{media_id}` - Partially update media file metadata
- `DELETE /api/media/{media_id}` - Delete media file record
- `POST /api/uploads` - Upload a file (separate endpoint, file service integration)

**Example POST/PUT Payload**:
```json
{
  "original_name": "document.pdf",
  "stored_name": "doc_12345.pdf",
  "file_path": "/uploads/courses/doc_12345.pdf",
  "file_url": "/uploads/courses/doc_12345.pdf",
  "mime_type": "application/pdf",
  "file_size": 120000,
  "uploaded_by": 1
}
```

**Status**: ✅ Complete with full CRUD + file upload

---

## 7. **Department - Course Hierarchy** (`courses.department_id`)

**Purpose**: Organize courses under departments

**Relationship**: One-to-Many (`department` → `courses`)

**Related Endpoints**:
- `GET /api/courses` - List all courses
- `GET /api/courses` with filter - Can filter by department
- `POST /api/courses` - Create course under a department

**Example Payload** (course creation):
```json
{
  "department_id": 1,
  "course_code": "CS101",
  "title": "Intro to Programming",
  "instructor_name": "Dr. Ali",
  "level": "undergraduate",
  "semester": "Spring 2026"
}
```

**Status**: ✅ Complete (managed through courses API)

---

## 8. **Department - Internship Hierarchy** (`internships.department_id`)

**Purpose**: Link internship opportunities to departments

**Relationship**: One-to-Many (`department` → `internships`)

**Related Endpoints**:
- `GET /api/internships` - List all internships
- `GET /api/internships` with filter - Can filter by department
- `POST /api/internships` - Create internship under a department

**Example Payload** (internship creation):
```json
{
  "department_id": 1,
  "title": "Summer Internship",
  "duration": "8 weeks",
  "start_date": "2026-06-01",
  "end_date": "2026-07-31"
}
```

**Status**: ✅ Complete (managed through internships API)

---

## 9. **Faculty - Department Hierarchy** (`departments.faculty_id`)

**Purpose**: Organize departments under faculties

**Relationship**: One-to-Many (`faculty` → `departments`)

**Related Endpoints**:
- `GET /api/departments` - List all departments
- `GET /api/departments` with filter - Can filter by faculty
- `POST /api/departments` - Create department under a faculty

**Example Payload** (department creation):
```json
{
  "faculty_id": 1,
  "name": "Software Engineering",
  "short_name": "SE",
  "department_type": "academic"
}
```

**Status**: ✅ Complete (managed through departments API)

---

## 10. **User - Media Upload Relationship** (`media_files.uploaded_by`)

**Purpose**: Track which user uploaded each media file

**Relationship**: One-to-Many (`user` → `media_files`)

**Related Endpoints**:
- `GET /api/media` - Get all media files (includes uploaded_by user ID)
- `GET /api/media/{media_id}` - Get specific file with uploader info
- `POST /api/media` - Register media with uploader info

**Status**: ✅ Complete (managed through media API)

---

## 11. **User - Role Relationship** (`users.role_id`)

**Purpose**: Assign roles/permissions to users

**Relationship**: Many-to-One (`users.role_id` → `roles.id`)

**Related Endpoints**:
- `GET /api/roles` - List roles
- `POST /api/roles/seed` - Create ADMIN, TEACHER, and STUDENT roles
- `POST /api/roles` - Create a new role (admin only)
- `GET /api/users` - List users with role info (admin only)
- `POST /api/users` - Create a user with role assignment
- `GET /api/users/{user_id}` - Get a user with role info (admin only)
- `PATCH /api/users/{user_id}/role` - Assign/change a user's role (admin only)

**Status**: ✅ Complete (managed through auth API)

---

## 12. **Teacher - Course Teaching Application** (`course_teaching_applications`)

**Purpose**: Let teachers apply for courses they want to teach, then let admin approve or reject.

**Relationship**: Many-to-Many with status (`teacher user` -> `course`)

**Related Endpoints**:
- `GET /api/course-teaching-applications` - Admin sees all, teacher sees own
- `POST /api/course-teaching-applications` - Teacher applies to teach a course
- `PATCH /api/course-teaching-applications/{application_id}/approve` - Admin approves teacher
- `PATCH /api/course-teaching-applications/{application_id}/reject` - Admin rejects teacher
- `GET /api/course-teaching-applications/teacher/{teacher_id}` - Applications by teacher
- `GET /api/course-teaching-applications/course/{course_id}` - Applications by course

**Example Payload**:
```json
{
  "course_id": 1,
  "message": "I want to teach this course"
}
```

**Status**: Complete with apply and approval flow

---

## 13. **Student - Course Enrollment/Application** (`course_enrollments`)

**Purpose**: Let students apply for courses. Admin or an approved teacher for that course can approve/reject. Approved students can see only approved course resources and lectures.

**Relationship**: Many-to-Many with status (`student user` -> `course`)

**Related Endpoints**:
- `GET /api/course-enrollments` - Admin sees all, teacher sees own approved-course enrollments, student sees own
- `POST /api/course-enrollments` - Student applies for a course
- `PATCH /api/course-enrollments/{enrollment_id}/approve` - Admin or approved teacher approves student
- `PATCH /api/course-enrollments/{enrollment_id}/reject` - Admin or approved teacher rejects student
- `GET /api/course-enrollments/student/{student_id}` - Enrollments by student
- `GET /api/course-enrollments/course/{course_id}` - Enrollments by course
- `GET /api/course-enrollments/me/courses` - Current user's approved/managed courses
- `GET /api/course-enrollments/me/resources` - Current user's visible course resources
- `GET /api/course-enrollments/me/lectures` - Current user's visible lectures

**Example Payload**:
```json
{
  "course_id": 1,
  "message": "I want to enroll in this course"
}
```

**Status**: Complete with apply, approval, and approved-resource visibility flow

---

## Summary Statistics

| Relationship Type | Count | Status |
|---|---|---|
| Pure Junction Tables | 1 (research_paper_authors) | ✅ |
| Linking Tables (with extended data) | 3 (lectures, course_resources, internship_resources) | ✅ |
| Self-Referencing Hierarchies | 1 (menu_items) | ✅ |
| File Tracking Relationships | 1 (media_files) | ✅ |
| User Upload Tracking | 1 (media_files.uploaded_by) | ✅ |
| One-to-Many Hierarchies | 4 (dept→course, dept→internship, fac→dept, user→media) | ✅ |

**Total Relationship APIs**: 32 endpoints across 11 relationship types

**All Status**: ✅ **COMPLETE** - All relationship APIs have full CRUD operations exposed in Swagger

---

## Swagger Access

All endpoints are documented and testable via Swagger UI:
- **Swagger UI**: `http://localhost:5000/apidocs`
- **OpenAPI JSON**: `http://localhost:5000/openapi.json`
- **Admin Dashboard**: `http://localhost:5000/admin`

Protected write/approval APIs use login tokens:
- `POST /api/roles/seed`
- `POST /api/auth/register`
- `POST /api/auth/login`
- Send `Authorization: Bearer <access_token>` for admin, teacher, and student actions.

Tag Groups in Swagger:
- **Core**: Auth, Roles, Users, Menu, Media
- **Academic**: Faculties, Departments, Courses, Course Resources, Lectures, Authors, Research Authors, Internships, Internship Resources, Research, Course Teaching Applications, Course Enrollments
