from app import create_app


def test_openapi_includes_routes_and_post_request_body():
    app = create_app()
    client = app.test_client()

    response = client.get('/openapi.json')

    assert response.status_code == 200
    spec = response.get_json()

    assert '/api/faculties' in spec['paths']
    assert 'get' in spec['paths']['/api/faculties']
    assert 'post' in spec['paths']['/api/faculties']
    assert 'requestBody' in spec['paths']['/api/faculties']['post']
    assert '/api/menu' in spec['paths']
    assert 'post' in spec['paths']['/api/menu']
    assert 'requestBody' in spec['paths']['/api/menu']['post']
    assert any(group['name'] == 'Core' for group in spec.get('x-tagGroups', []))
