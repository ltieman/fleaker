"""Unit tests for the custom test client in Fleaker."""

from flask import jsonify, request


def test_test_client_json_kwarg(app, client):
    @app.route('/login', methods=['POST'])
    def login():
        data = request.get_json()
        assert 'email' in data
        assert 'password' in data

        return jsonify({'message': 'User logged in!'}), 201

    resp = client.post(
        '/login',
        json={
            'email': 'bob@example.com',
            'password': 'correct horse battery staple'
        }
    )

    assert resp.status_code == 201
    assert 'message' in resp.json
