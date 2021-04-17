"""Message model tests."""

import os
from unittest import TestCase
from sqlalchemy import exc

from models import db, User, Message, Follows, Likes

os.environ["DATABASE_URL"] = "postgresql:///warbler-test"

from app import app, CURR_USER_KEY

app.config["WTF_CSRF_ENABLED"] = False

import pdb


class MessageTestCase(TestCase):
    """Test views for messages."""

    @classmethod
    def setUpClass(cls):
        # runs before test suite begins
        return ""

    def setUp(self):
        """Create test client, add sample data."""

        db.session.close()
        db.drop_all()
        db.create_all()

        self.client = app.test_client()

        self.testuser = User.signup(
            username="testuser",
            email="test@test.com",
            password="testuser",
            image_url=None,
        )

        self.testuser2 = User.signup(
            username="testuser2",
            email="test2@test.com",
            password="testuser2",
            image_url=None,
        )

        db.session.commit()

    def tearDown(self):
        resp = super().tearDown()
        db.session.rollback()
        return resp

    def testMessageCreation(self):
        """Test creating a message"""
        user = User.query.filter_by(email="test@test.com").first()
        test_message = Message(text="This is a test message", user_id=user.id)
        db.session.add(test_message)
        db.session.commit()

        self.assertIsNotNone(
            Message.query.filter_by(text="This is a test message").first()
        )

    def testMessageToUserRelationship(self):
        """Test SQLAlchemy relationship between message and user"""
        user = User.query.filter_by(email="test@test.com").first()
        test_message = Message(text="This is a test message", user_id=user.id)
        db.session.add(test_message)
        db.session.commit()

        self.assertEqual(test_message.user, user)

    def testLikingMessage(self):
        """Test liking and unliking a message"""
        # login and create a post as first testuser
        with self.client as c, app.app_context():
            c.post(
                "/login",
                data={
                    "username": self.testuser.username,
                    "password": self.testuser.password,
                },
            )
            with c.session_transaction() as sess:
                sess[CURR_USER_KEY] = self.testuser.id
            test_message = Message(
                text="This is a test message", user_id=self.testuser.id
            )
            db.session.add(test_message)
            db.session.commit()
            # next, need to logout then login as testuser2

            c.get("/logout", follow_redirects=True)

            c.post(
                "/login",
                data={
                    "username": self.testuser2.username,
                    "password": self.testuser2.password,
                },
            )
            with c.session_transaction() as sess:
                sess[CURR_USER_KEY] = self.testuser2.id

            # like the post from testuser while logged in as testuser2
            resp = c.post("/users/toggle_like/1")
            check_for_like = Likes.query.filter_by(
                user_id=self.testuser2.id, message_id=1
            ).first()
            self.assertIsNotNone(check_for_like)

            # try post request to same link to unlike message

            resp = c.post("/users/toggle_like/1")
            # now we should get None if we check DB for the same like
            check_for_like = Likes.query.filter_by(
                user_id=self.testuser2.id, message_id=1
            ).first()
            self.assertIsNone(check_for_like)