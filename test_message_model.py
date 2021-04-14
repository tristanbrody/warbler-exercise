"""Message model tests."""

import os
from unittest import TestCase
from sqlalchemy import exc

from models import db, User, Message, Follows

os.environ['DATABASE_URL'] = "postgresql:///warbler-test"

from app import app

db.create_all()

class MessageTestCase(TestCase):
    """Test views for messages."""

    @classmethod
    def setUpClass(cls):
        #runs before test suite begins
        return ''

    def setUp(self):
        """Create test client, add sample data."""

        User.query.delete()
        Message.query.delete()
        Follows.query.delete()

        user = User(
            email="test@test.com",
            username="testuser",
            password="HASHED_PASSWORD"
        )
        db.session.add(user)
        db.session.commit()

        self.client = app.test_client()
    
    def testMessageCreation(self):
        """Test creating a message"""
        user = User.query.filter_by(email='test@test.com').first()
        test_message = Message(text="This is a test message",user_id=user.id)
        db.session.add(test_message)
        db.session.commit()

        self.assertIsNotNone(Message.query.filter_by(text='This is a test message').first())

    def testMessageToUserRelationship(self):
        """Test SQLAlchemy relationship between message and user"""
        user = User.query.filter_by(email='test@test.com').first()
        test_message = Message(text="This is a test message",user_id=user.id)
        db.session.add(test_message)
        db.session.commit()

        self.assertEqual(test_message.user, user)  