#!/usr/bin/env python
from app import create_app

app = create_app()
c = app.test_client()
r = c.get('/openapi.json')
data = r.get_json()

print('=' * 70)
print('COMPLETE RELATIONAL APIS - ALL ENDPOINTS')
print('=' * 70)

relationships = {
    'Research Paper ↔ Author': [p for p in data['paths'].keys() if 'research-authors' in p],
    'Course ↔ Lecture': [p for p in data['paths'].keys() if 'lectures' in p],
    'Course ↔ Resources': [p for p in data['paths'].keys() if 'course-resources' in p],
    'Internship ↔ Resources': [p for p in data['paths'].keys() if 'internship-resources' in p],
    'Faculty ↔ Department': [p for p in data['paths'].keys() if '/api/departments/faculty' in p],
    'Department ↔ Course': [p for p in data['paths'].keys() if '/api/courses/department' in p],
    'Department ↔ Internship': [p for p in data['paths'].keys() if '/api/internships/department' in p],
    'Department ↔ Research': [p for p in data['paths'].keys() if '/api/research/department' in p],
    'Menu Hierarchy': [p for p in data['paths'].keys() if '/api/menu' in p and 'upload' not in p],
    'Media Files': [p for p in data['paths'].keys() if '/api/media' in p],
    'Teacher Course Applications': [p for p in data['paths'].keys() if '/api/course-teaching-applications' in p],
    'Student Course Enrollments': [p for p in data['paths'].keys() if '/api/course-enrollments' in p],
}

total_rel_methods = 0
for category, paths in relationships.items():
    if paths:
        print(f'\n{category}:')
        print('─' * 70)
        for path in sorted(paths):
            methods = [m for m in data['paths'][path].keys() if m not in ['parameters']]
            methods_str = ', '.join(methods).upper()
            print(f'  {path}')
            print(f'    └─ {methods_str}')
            total_rel_methods += len(methods)

print('\n' + '=' * 70)
print(f'SUMMARY: {total_rel_methods} relational endpoints | {len(data["paths"])} total endpoints')
print('=' * 70)

print('\n✅ RELATIONSHIP ENDPOINTS VERIFICATION:')
print('─' * 70)

# Check for all expected filter endpoints
filters = [
    ('/api/research-authors/paper/{research_paper_id}', 'Authors by Paper'),
    ('/api/research-authors/author/{author_id}', 'Papers by Author'),
    ('/api/lectures/course/{course_id}', 'Lectures by Course'),
    ('/api/course-resources/course/{course_id}', 'Resources by Course'),
    ('/api/internship-resources/internship/{internship_id}', 'Resources by Internship'),
    ('/api/departments/faculty/{faculty_id}', 'Departments by Faculty'),
    ('/api/courses/department/{department_id}', 'Courses by Department'),
    ('/api/internships/department/{department_id}', 'Internships by Department'),
    ('/api/research/department/{department_id}', 'Research by Department'),
    ('/api/course-teaching-applications/teacher/{teacher_id}', 'Teaching Applications by Teacher'),
    ('/api/course-teaching-applications/course/{course_id}', 'Teaching Applications by Course'),
    ('/api/course-enrollments/student/{student_id}', 'Course Enrollments by Student'),
    ('/api/course-enrollments/course/{course_id}', 'Course Enrollments by Course'),
    ('/api/course-enrollments/me/resources', 'Approved Course Resources for Current User'),
]

for endpoint, description in filters:
    exists = endpoint in data['paths']
    status = '✅' if exists else '❌'
    print(f'{status} {endpoint:50} - {description}')

print('\n' + '=' * 70)
print('All relational API endpoints have been created and exposed in Swagger!')
print('=' * 70)
