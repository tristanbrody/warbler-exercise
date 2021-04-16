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

os.environ['DATABASE_URL'] = "postgresql:///warbler-test"


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
        #runs before test suite begins
        return ''

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

        u = User(
            email="test@test.com",
            username="testuser",
            password="HASHED_PASSWORD"
        )

        db.session.add(u)
        db.session.commit()

        # test that __repr__ method on user works as expected
        u_repr = u.__repr__()
        self.assertIn(f'User #{u.id}: {u.username}, {u.email}', u_repr)

        # User should have no messages & no followers
        self.assertEqual(len(u.messages), 0)
        self.assertEqual(len(u.followers), 0)
    
    def test_following_methods(self):
        """Do is_following and is_followed user methods work?"""
        user_1 = User(
            email="test@test.com",
            username="testuser",
            password="HASHED_PASSWORD"
        )
        user_2 = User(
            email="test2@test.com",
            username="testuser2",
            password="HASHED_PASSWORD"
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
        User.signup('bobs_burgers', 'test@test.com', 'testing1!', '')
        db.session.commit()
        new_user = User.query.filter_by(email='test@test.com').first()
        self.assertIsNotNone(new_user)
        try: 
            User.signup('dans_the_man', 'test@test.com', 'testing2', '')
            db.session.commit()
        #should throw a SQLAlchemy error for trying to insert a user with an existing primary key
        except :
            new_user2 = User.query.filter_by(username='dans_the_man').first()
            self.assertEqual(None, new_user2)
