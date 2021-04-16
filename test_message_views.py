"""Message View tests."""

# run these tests like:
#
#    FLASK_ENV=production python -m unittest test_message_views.py


import os
from unittest import TestCase

from models import db, connect_db, Message, User
import pdb

# BEFORE we import our app, let's set an environmental variable
# to use a different database for tests (we need to do this
# before we import our app, since that will have already
# connected to the database

os.environ['DATABASE_URL'] = "postgresql:///warbler-test"


# Now we can import app

from app import app, CURR_USER_KEY

# Create our tables (we do this here, so we only create the tables
# once for all tests --- in each test, we'll delete the data
# and create fresh new clean test data

db.create_all()

# Don't have WTForms use CSRF at all, since it's a pain to test

app.config['WTF_CSRF_ENABLED'] = False


class MessageViewTestCase(TestCase):
    """Test views for messages."""

    def setUp(self):
        """Create test client, add sample data."""

        db.session.close()
        db.drop_all()
        db.create_all()

        self.client = app.test_client()

        self.testuser = User.signup(username="testuser",
                                    email="test@test.com",
                                    password="testuser",
                                    image_url=None)

        self.testuser2 = User.signup(username="testuser2",
                                    email="test2@test.com",
                                    password="testuser2",
                                    image_url=None)

        db.session.commit()

    def tearDown(self):
        resp = super().tearDown()
        db.session.rollback()
        return resp

    def test_add_message(self):
        """Can users add a message?"""

        # Since we need to change the session to mimic logging in,
        # we need to use the changing-session trick:

        with self.client as c:
            with c.session_transaction() as sess:
                sess[CURR_USER_KEY] = self.testuser.id

            resp = c.post("/messages/new", data={"text": "Hello"}, follow_redirects=True)

            self.assertEqual(resp.status_code, 200)

            msg = Message.query.one()
            self.assertEqual(msg.text, "Hello")

    def test_view_message(self):
        #first create a message
        with self.client as c:
            with c.session_transaction() as sess:
                sess[CURR_USER_KEY] = self.testuser.id
            
            c.post("/messages/new", data={"text": "Hi there"}, follow_redirects=True)
            # get the message we just created
            new_message = Message.query.filter_by(user_id=self.testuser.id).first()
            resp = c.get(f'/messages/{new_message.id}')
            self.assertEqual(resp.status_code, 200)
            self.assertIn(b"Hi there", resp.data)

    def test_delete_message(self):
        """Test creating then deleting a message"""            
        #first create message
        with self.client as c, app.app_context():
            with c.session_transaction() as sess:
                sess[CURR_USER_KEY] = self.testuser.id
            c.post("/messages/new", data={"text": "Hi there"}, follow_redirects=True)
            # get the message we just created
            new_message = Message.query.filter_by(user_id=self.testuser.id).first()
            resp = c.post(f'/messages/{new_message.id}/delete', follow_redirects=False)
            check_for_message_again = Message.query.filter_by(user_id=self.testuser.id).first()
            
            #second SQLAlchemy select should have returned None after delete
            self.assertIsNone(check_for_message_again)
            self.assertEqual(resp.status_code, 302)
            # make sure we were redirected after delete
            self.assertIn(f'/users/{self.testuser.id}', resp.location)

    def test_unauthorized_logged_out_delete_message(self):
        """Test deleting a message while logged out"""
        #first create message
        with self.client as c, app.app_context():
            with c.session_transaction() as sess:
                sess[CURR_USER_KEY] = self.testuser.id
            c.post("/messages/new", data={"text": "Hi there"}, follow_redirects=True)
            # get the message we just created
            new_message = Message.query.filter_by(user_id=self.testuser.id).first()
            # then log out
            c.get('/logout')
            # then try to delete message we created
            resp = c.post(f'/messages/{new_message.id}/delete', follow_redirects=True)
            self.assertIn(b"Access unauthorized", resp.data)
    
    def test_unauthorized_logged_in_delete_message(self):
        """Test deleting a message logged-in user did not post"""
        #first create message
        with self.client as c, app.app_context():
            with c.session_transaction() as sess:
                sess[CURR_USER_KEY] = self.testuser.id
            c.post("/messages/new", data={"text": "Hi there"}, follow_redirects=True)
            # get the message we just created
            new_message = Message.query.filter_by(user_id=self.testuser.id).first()
            # then log out
            c.get('/logout')
            # then edit session and login as another user
            with c.session_transaction() as sess:
                sess[CURR_USER_KEY] = self.testuser2.id
            self.client.post('/login', data={
                    'username': self.testuser2.username,
                    'password': self.testuser2.password
            }, follow_redirects=True)
            resp = c.post(f'/messages/{new_message.id}/delete', follow_redirects=True)
            self.assertIn(b"Access unauthorized", resp.data)

    def test_unauthorized_create_message(self):
        """Test posting a message while logged out"""
        # first make sure we're logged out
        with self.client as c, app.app_context():
            c.get('/logout')
            resp = c.post("/messages/new", data={"text": "uh oh this shouldn't work"}, follow_redirects=True)
            self.assertIn(b'Access unauthorized', resp.data)