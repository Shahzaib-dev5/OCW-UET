from app import create_app


def test_lectures_are_listed_in_openapi():
    app = create_app()
    client = app.test_client()

    response = client.get('/openapi.json')

    assert response.status_code == 200
    spec = response.get_json()
    assert '/api/lectures' in spec['paths']
    assert 'post' in spec['paths']['/api/lectures']
    assert 'get' in spec['paths']['/api/lectures']
    assert any(tag['name'] == 'Lectures' for tag in spec['tags'])
