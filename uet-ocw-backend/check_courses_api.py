#!/usr/bin/env python
from app import create_app

app = create_app()
c = app.test_client()
r = c.get('/openapi.json')
data = r.get_json()

print('=== COURSES API ENDPOINTS ===\n')

courses_paths = sorted([p for p in data['paths'].keys() if 'courses' in p])
for path in courses_paths:
    methods = [m for m in data['paths'][path].keys() if m not in ['parameters']]
    print(f'{path}')
    print(f'  Methods: {", ".join(methods).upper()}')
    if 'department' in path:
        print(f'  ✅ Filter by Department: YES')
    print()

print('=== HOW TO FETCH COURSES BY DEPARTMENT ===\n')
print('Endpoint: GET /api/courses/department/{department_id}')
print('\nExample:')
print('  curl http://localhost:5000/api/courses/department/1')
print('\nResponse:')
print('  {')
print('    "status": "success",')
print('    "data": [')
print('      {')
print('        "id": 1,')
print('        "department_id": 1,')
print('        "course_code": "CS101",')
print('        "title": "Intro to Programming",')
print('        ...')
print('      }')
print('    ]')
print('  }')
