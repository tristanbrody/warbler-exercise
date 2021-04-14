"""User views tests."""

import os
from unittest import TestCase
from sqlalchemy import exc
import pdb

from models import db, User, Message, Follows

os.environ['DATABASE_URL'] = "postgresql:///warbler-test"

from app import app, CURR_USER_KEY
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
    
    def testSuccessfulLogin(self):
        """test for successful login"""
        data = {
            "username": "new_user",
            "password": "some_password",
            "email": "myemail@yahoo.com"
        }
        # first need to sign up
        self.client.post('/signup', data=data, follow_redirects=True)
        user = User.query.filter_by(username='new_user')
        response = self.client.post('/login', data={
            'username': 'new_user',
            'password': 'some_password'
        }, follow_redirects=True)
        self.assertEqual(response.status_code, 200)
        self.assertIn(b'Hello, new_user', response.data)

    def testFailedLogin(self):
        """test for failed login"""
        response = self.client.post('/login', data={
            'username': self.testuser.username,
            'password': 'wrongpassword'
        }, follow_redirects=True)

        self.assertEqual(response.status_code, 200)
        self.assertIn(b'Invalid credentials', response.data)

    def testSuccessfulLogout(self):
        """test for successful logout for logged-in user"""
        data = {
                    "username": "new_user",
                    "password": "some_password",
                    "email": "myemail@yahoo.com"
                }
        # first need to sign up
        self.client.post('/signup', data=data, follow_redirects=True)
        user = User.query.filter_by(username='new_user').first()
        #then need to log in
        self.client.post('/login', data={'username': user.username,'password': user.password}, follow_redirects=True)

        #need to add signed-in user id to fake session
        with self.client as c:
            with c.session_transaction() as sess:
                sess[CURR_USER_KEY] = user.id
        
        #then finally can try to log out
        response = self.client.get('/logout', follow_redirects=True)

        self.assertEqual(response.status_code, 200)
        self.assertIn(b'You have been logged out', response.data)

    def testUsersPage(self):
        """test users page is being rendered as expected"""

        #try searching for a specific user with querystring
        response = self.client.get('/users?q=testuser')

        self.assertEqual(response.status_code, 200)
        self.assertIn(b'testuser', response.data)

    def testUserDetailsPage(self):
        """test details page for a specific user"""
    
        response = self.client.get(f'/users/{self.testuser.id}')
        self.assertEqual(response.status_code, 200)
        self.assertIn(b'testuser', response.data)

        #check for 404 for an id that doesn't exist

        response = self.client.get('/users/200')
        self.assertEqual(response.status_code, 404)
    
    #TODO get this test to work - see about using g object with tests
    # def testAddingFollowedUser(self):
    #     """Test following a new user"""

    #     self.user = self.signUpAndLogin()
    #     response = self.client.post(f'/users/follow/{self.testuser.id}', follow_redirects=True)

    #     self.assertEqual(response.status_code, 200)

    #TODO if this function works as expected, refactor some of the tests above
    def signUpAndLogin(self):
        data = {
                    "username": "new_user",
                    "password": "some_password",
                    "email": "myemail@yahoo.com"
                }
        # first need to sign up
        self.client.post('/signup', data=data, follow_redirects=True)
        user = User.query.filter_by(username='new_user').first()
        #then need to log in
        self.client.post('/login', data={'username': user.username,'password': user.password}, follow_redirects=True)    
        return user