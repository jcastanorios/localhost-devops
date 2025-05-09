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


  
    def test_add_to_blacklist_invalid_token_format(self):
        with self.app.test_client() as client:
            response = client.post('/blacklists', json={"token": "123"},  
                                   headers={'Content-Type': 'application/json'})
            self.assertEqual(response.status_code, 400)
            self.assertIn('error', response.json)
            self.assertEqual(response.json['error'], 'Invalid token format')

    def test_invalid_email_format(self):
        with self.app.app_context():
            response, status = BlacklistService.add_to_blacklist(
                email="invalid.email@",  # Invalid email format
                app_uuid="test-app-uuid",
                blocked_reason="test reason",
                ip_address="127.0.0.1"
            )
            self.assertEqual(status, 400)
            self.assertEqual(response.get_json()['error'], 'Invalid email format')

    def test_invalid_ip_format(self):
        with self.app.app_context():
            response, status = BlacklistService.add_to_blacklist(
                email="valid@email.com",
                app_uuid="test-app-uuid",
                blocked_reason="test reason",
                ip_address="999.999.999.999"  
            )
            self.assertEqual(status, 400)
            self.assertEqual(response.get_json()['error'], 'Invalid IP address format')

    def test_duplicate_email(self):
        with self.app.app_context():
            # Primer intento de agregar el email
            BlacklistService.add_to_blacklist(
                email="test@example.com",
                app_uuid="test-app-uuid",
                blocked_reason="test reason",
                ip_address="127.0.0.1"
            )
            
           
            response, status = BlacklistService.add_to_blacklist(
                email="test@example.com",
                app_uuid="test-app-uuid",
                blocked_reason="another reason",
                ip_address="127.0.0.1"
            )
            
            self.assertEqual(status, 400)
            self.assertEqual(response.get_json()["msg"], "El email ya está en la lista negra")

    def test_empty_blocked_reason(self):
        with self.app.app_context():
            response, status = BlacklistService.add_to_blacklist(
                email="test@example.com",
                app_uuid="test-app-uuid",
                blocked_reason="",  # Razón de bloqueo vacía
                ip_address="127.0.0.1"
            )
            self.assertEqual(status, 400)
            self.assertEqual(response.get_json()['error'], 'La razón de bloqueo no puede estar vacía')

    def test_long_blocked_reason(self):
        with self.app.app_context():
            response, status = BlacklistService.add_to_blacklist(
                email="test@example.com",
                app_uuid="test-app-uuid",
                blocked_reason="x" * 501,  # Razón de bloqueo de más de 500 caracteres
                ip_address="127.0.0.1"
            )
            self.assertEqual(status, 400)
            self.assertEqual(response.get_json()['error'], 'La razón de bloqueo no puede exceder 500 caracteres')

    def test_empty_app_uuid(self):
        with self.app.app_context():
            response, status = BlacklistService.add_to_blacklist(
                email="test@example.com",
                app_uuid="",  # app_uuid vacío
                blocked_reason="test reason",
                ip_address="127.0.0.1"
            )
            self.assertEqual(status, 400)
            self.assertEqual(response.get_json()['error'], 'El app_uuid no puede estar vacío')

    def test_invalid_app_uuid_format(self):
        with self.app.app_context():
            response, status = BlacklistService.add_to_blacklist(
                email="test@example.com",
                app_uuid="invalid-uuid-format",  # Formato inválido de UUID
                blocked_reason="test reason",
                ip_address="127.0.0.1"
            )
            self.assertEqual(status, 400)
            self.assertEqual(response.get_json()['error'], 'Formato de app_uuid inválido')

    def test_email_with_special_chars(self):
        with self.app.app_context():
            response, status = BlacklistService.add_to_blacklist(
                email="test<script>@example.com",  # Email con caracteres especiales no permitidos
                app_uuid="test-app-uuid",
                blocked_reason="test reason",
                ip_address="127.0.0.1"
            )
            self.assertEqual(status, 400)
            self.assertEqual(response.get_json()['error'], 'El email contiene caracteres no permitidos')