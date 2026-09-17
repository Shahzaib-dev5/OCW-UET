from io import BytesIO

from app import create_app


def test_upload_route_saves_file_locally():
    app = create_app()
    client = app.test_client()

    response = client.post(
        '/api/uploads',
        data={
            'file': (BytesIO(b'hello world'), 'notes.txt'),
            'folder': 'courses/1/resources',
        },
        content_type='multipart/form-data',
    )

    assert response.status_code == 200, response.get_data(as_text=True)
    payload = response.get_json()

    assert payload['status'] == 'success'
    assert payload['local_url'].startswith('/uploads/')
    assert payload['filename'].endswith('.txt')
