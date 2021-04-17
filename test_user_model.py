"""User model tests."""

# run these tests like:
#
#    python -m unittest test_user_model.py


import os
from unittest import TestCase
from psycopg2 import errors

from models import db, User, Message, Follows
import pdb

# BEFORE we import our app, let's set an environmental variable
# to use a different database for tests (we need to do this
# before we import our app, since that will have already
# connected to the database

os.environ["DATABASE_URL"] = "postgresql:///warbler-test"


# Now we can import app

from app import app

# Create our tables (we do this here, so we only create the tables
# once for all tests --- in each test, we'll delete the data
# and create fresh new clean test data

db.create_all()


class UserModelTestCase(TestCase):
    """Test views for messages."""

    @classmethod
    def setUpClass(cls):
        # runs before test suite begins
        return ""

    def setUp(self):
        """Create test client, add sample data."""

        db.drop_all()
        db.create_all()

        self.client = app.test_client()

    def tearDown(self):
        resp = super().tearDown()
        db.session.rollback()
        return resp

    def test_user_model(self):
        """Does basic model work?"""

        u = User(email="test@test.com", username="testuser", password="HASHED_PASSWORD")

        db.session.add(u)
        db.session.commit()

        # test that __repr__ method on user works as expected
        u_repr = u.__repr__()
        self.assertIn(f"User #{u.id}: {u.username}, {u.email}", u_repr)

        # User should have no messages & no followers
        self.assertEqual(len(u.messages), 0)
        self.assertEqual(len(u.followers), 0)

    def test_following_methods(self):
        """Do is_following and is_followed user methods work?"""
        user_1 = User(
            email="test@test.com", username="testuser", password="HASHED_PASSWORD"
        )
        user_2 = User(
            email="test2@test.com", username="testuser2", password="HASHED_PASSWORD"
        )
        db.session.add_all([user_1, user_2])
        db.session.commit()

        follow = Follows(user_being_followed_id=user_1.id, user_following_id=user_2.id)
        db.session.add(follow)
        db.session.commit()

        self.assertTrue(user_1.is_followed_by(user_2))
        self.assertFalse(user_2.is_followed_by(user_1))
        self.assertTrue(user_2.is_following(user_1))
        self.assertFalse(user_1.is_following(user_2))

    def test_user_creation(self):
        """Test user creation class method"""
        User.signup("bobs_burgers", "test@test.com", "testing1!", "")
        db.session.commit()
        new_user = User.query.filter_by(email="test@test.com").first()
        self.assertIsNotNone(new_user)

    def testAuthenticate(self):
        """Test authorized and unauthorized login with authenticate class method"""

        # first sign up a new user
        self.testuser = User.signup(
            username="testuser",
            email="test@test.com",
            password="testuser",
            image_url=None,
        )

        db.session.commit()

        authentication_attempt = User.authenticate(self.testuser.username, "testuser")
        # this should be successful and return the user
        test = User.query.get(self.testuser.id)
        self.assertEqual(authentication_attempt, self.testuser)
        authentication_attempt = User.authenticate(
            self.testuser.username, self.testuser.password + "x"
        )
        # this should be unsuccessful and return False
        self.assertFalse(authentication_attempt)

    # def testChangePassword(self):
    #     """Test changing password with class method"""

    #     # first sign up as a new user
    #     self.testuser = User.signup(
    #         username="testuser",
    #         email="test@test.com",
    #         password="testuser",
    #         image_url=None,
    #     )

    #     db.session.commit()

    #     # now try to change password

    #     test_change_password = User.change_password(
    #         self.testuser.username, self.testuser.password, "mynewpassword"
    #     )

    #     # this should be successful and return the user

    #     self.assertEqual(self.testuser, test_change_password)


# TODO fix this test
