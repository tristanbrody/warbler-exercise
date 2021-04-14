"""User views tests."""

import os
from unittest import TestCase
from sqlalchemy import exc
import pdb

from models import db, User, Message, Follows

os.environ['DATABASE_URL'] = "postgresql:///warbler-test"

from app import app
app.config['WTF_CSRF_ENABLED'] = False

db.create_all()

class UserViewTestCase(TestCase):
    """Test views for user routes."""

    def setUp(self):
        """Create test client, add sample data."""

        User.query.delete()
        Message.query.delete()

        self.client = app.test_client()

        self.testuser = User.signup(username="testuser",
                                    email="test@test.com",
                                    password="testuser",
                                    image_url=None)

        db.session.commit()
    
    def testSignUp(self):
        data = {
            "username": "new_user",
            "password": "some_password",
            "email": "myemail@yahoo.com"
        }
        response = self.client.post('/signup', data=data, follow_redirects=True)
        user = User.query.filter_by(username='new_user')

        self.assertIn(b'Congrats on signing up', response.data)

        self.assertIsNotNone(user)

        self.assertEqual(response.status_code, 200)