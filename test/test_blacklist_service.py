import unittest
from unittest.mock import patch, MagicMock
from flask import Flask, jsonify, request
from flask_sqlalchemy import SQLAlchemy
from extensions.database import db
from core.blacklist_service import BlacklistService

class BlacklistServiceTest(unittest.TestCase):

    def setUp(self):
        self.app = Flask(__name__)
        self.app.config['TESTING'] = True
        self.app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///:memory:'
        self.app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
        with self.app.app_context():
            db.init_app(self.app)
            db.create_all()

            # Ruta para simular el comportamiento de la blacklist
            @self.app.route('/blacklists', methods=['POST'])
            def blacklist():
                data = request.get_json()
                if not data or not data.get('token'):
                    return jsonify({'error': 'Missing data'}), 400
                # Aquí llamamos al método de la clase BlacklistService que está mockeada
                result = BlacklistService.add_to_blacklist(data.get('token'), 'test-app-uuid', 'test-reason', '127.0.0.1')

                if result:
                    return jsonify({'message': 'Token blacklisted'}), 200
                else:
                    return jsonify({'error': 'Failed to blacklist'}), 400

    def tearDown(self):
        with self.app.app_context():
            db.session.remove()
            db.drop_all()
        self.app = None

    @patch('core.blacklist_service.BlacklistService.add_to_blacklist')
    def test_add_to_blacklist_failure(self, mock_add):
        mock_add.return_value = False

        response = self.app.test_client().post('/blacklists', json={},
                                            headers={'Content-Type': 'application/json'})

        self.assertEqual(response.status_code, 400)
        self.assertIn('error', response.json)


    @patch('core.blacklist_service.BlacklistService.add_to_blacklist')
    def test_add_to_blacklist_success(self, mock_add):
        mock_add.return_value = True

        response = self.app.test_client().post('/blacklists', json={"token": "abc123"},
                                            headers={'Content-Type': 'application/json'})

        self.assertEqual(response.status_code, 200)
        self.assertIn('message', response.json)

        mock_add.assert_called_once_with("abc123", 'test-app-uuid', 'test-reason', '127.0.0.1')

    def test_check_blacklist_found(self):
        with self.app.app_context():
            BlacklistService.add_to_blacklist(
                email="blacklisted@example.com",
                app_uuid="app-uuid",
                blocked_reason="reason",
                ip_address="127.0.0.1"
            )
            response, status = BlacklistService.check_blacklist("blacklisted@example.com")

            self.assertEqual(status, 200)
            self.assertTrue(response.get_json()["is_blacklisted"])
    

    def test_check_blacklist_not_found(self):
        with self.app.app_context():
            response, status = BlacklistService.check_blacklist("notfound@example.com")

            self.assertEqual(status, 200)
            self.assertFalse(response.get_json()["is_blacklisted"])

