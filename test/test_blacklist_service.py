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


    @patch('core.blacklist_service.BlacklistService.query.filter_by')
    def test_check_blacklist_email_in_list(self, mock_filter_by):
        mock_blacklist_entry = MagicMock()
        mock_blacklist_entry.blocked_reason = "Spam"
        mock_filter_by.return_value.first.return_value = mock_blacklist_entry
        email = "test@example.com"
        
        with self.app.app_context():  # Aseguramos que el contexto de la aplicación esté disponible
            response = BlacklistService.check_blacklist(email)
        
        self.assertEqual(response[1], 200)
        self.assertIn("is_blacklisted", response[0].get_data(as_text=True))
        self.assertTrue("is_blacklisted" in response[0].get_json())
        self.assertTrue(response[0].get_json()["is_blacklisted"])

    @patch('core.blacklist_service.BlacklistService.query.filter_by')
    def test_check_blacklist_email_not_in_list(self, mock_filter_by):
        mock_filter_by.return_value.first.return_value = None
        email = "test@example.com"
        
        with self.app.app_context():
            response = BlacklistService.check_blacklist(email)
        
        self.assertEqual(response[1], 200)
        self.assertIn("is_blacklisted", response[0].get_data(as_text=True))
        self.assertFalse(response[0].get_json()["is_blacklisted"])

if __name__ == '__main__':
    unittest.main()
