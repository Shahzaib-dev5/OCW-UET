from app import create_app


def test_authors_are_listed_in_openapi():
    app = create_app()
    client = app.test_client()

    response = client.get('/openapi.json')

    assert response.status_code == 200
    spec = response.get_json()
    assert '/api/authors' in spec['paths']
    assert 'post' in spec['paths']['/api/authors']
    assert 'get' in spec['paths']['/api/authors']
    assert any(tag['name'] == 'Authors' for tag in spec['tags'])
