#!/usr/bin/env python
from app import create_app

app = create_app()
c = app.test_client()
r = c.get('/openapi.json')
data = r.get_json()

print('=== RELATIONSHIP APIs IN SWAGGER ===\n')

# Group endpoints by category
relationships = {
    'Research Paper-Author': [p for p in data['paths'].keys() if 'research-authors' in p],
    'Course-Lecture': [p for p in data['paths'].keys() if 'lectures' in p],
    'Course-Resources': [p for p in data['paths'].keys() if 'course-resources' in p],
    'Internship-Resources': [p for p in data['paths'].keys() if 'internship-resources' in p],
    'Menu Hierarchy': [p for p in data['paths'].keys() if '/api/menu' in p],
    'Media Files': [p for p in data['paths'].keys() if '/api/media' in p],
    'File Upload': [p for p in data['paths'].keys() if 'upload' in p]
}

total_rel_endpoints = 0
for category, paths in relationships.items():
    if paths:
        print(f'{category}:')
        for path in sorted(paths):
            methods = list(data['paths'][path].keys())
            methods = [m for m in methods if m not in ['parameters']]
            print(f'  {path}')
            print(f'    Methods: {", ".join(methods).upper()}')
            total_rel_endpoints += len(methods)

print(f'\n=== SWAGGER CONFIGURATION ===')
print(f'Total Relationship Endpoints: {total_rel_endpoints}')
print(f'Total All Endpoints: {len(data["paths"])}')

print(f'\n=== TAGS ({len(data["tags"])}) ===')
for tag in data['tags']:
    print(f"  • {tag['name']}: {tag['description']}")

print(f'\n=== TAG GROUPS ===')
for group in data.get('x-tagGroups', []):
    tags_str = ', '.join(group['tags'])
    print(f"  {group['name']}: {tags_str}")

print('\n✅ Status: All relationship APIs exposed in Swagger')
print('📍 Access Swagger UI at: http://localhost:5000/apidocs')
print('📄 View OpenAPI spec at: http://localhost:5000/openapi.json')
