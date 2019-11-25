#!/usr/bin/env python
# -*- coding: utf-8 -*-
# Filename: users/routes.py

import hashlib, secrets, binascii, logging, uuid, ipaddress, datetime

from pycnic.core import Handler

from sqlalchemy.orm import sessionmaker

from settings import hash_iterations

from util.decorators import requires_params, requires_login
from util.util import BaseHandler

from users.models import User
from users.util import *

logger = logging.getLogger(__name__)
logging.basicConfig(level=logging.INFO)

class UsersRoutes(BaseHandler):
    """Route handler for requests about users."""
    def get(self, username=None):
        """GET /users/<username>
        Echoes the specified username, if it exists.

        Arguments:
            username (str): Username to access the information of.
        """
        user = fetch_user_by_username(username)
        if not user:
            return self.HTTP_404(error='User not found.')
        return self.HTTP_200(data={'username': username})

class Login(BaseHandler):
    """Route handler for login requests."""
    @requires_params('email', 'password')
    def post(self):
        """POST /login
        Attempt to authenticate a user.

        Parameters:
            email (str): Email address being used to authenticate.
            password (str): Password being used to authenticate.
        """
        email = self.request.data['email']
        input_password = self.request.data['password']
        ip = ipaddress.ip_address(self.request.ip)

        user = fetch_user_by_email(email)

        if login_attempts_exceeded(email):
           logger.warn(f'User with email {email} tried to login too many times. Rate limiting applied.')
           return self.HTTP_429(data={'msg': 'Too many failed login attempts. Please try again later.'})

        # We check all of these things before returning to prevent account enumeration via timing attacks.
        forbidden = False
        if not user:
            log_login_attempt(email, False, ip)
            logger.warn(f'Tried to log in with email {email}, but this email is not registered.')
            forbidden = True

        if user and (not user.password_hash):
            log_login_attempt(email, False, ip)
            logger.warn(f'Tried to log in with email {email}, but this account has not completed registration.')
            forbidden = True

        if user and user.password_hash and (not check_password(input_password, user.password_hash)):
            log_login_attempt(email, False, ip)
            logger.warn(f'Tried to log in with email {email}, but input password did not match stored password.')
            forbidden = True

        if forbidden:
            return self.HTTP_403(error='Login failed.')

        logger.info(f'User {user.username} logged in.')
        log_login_attempt(email, True, ip)

        # Generate a session token for the user, and set their session cookie.
        session_token = create_session_token(user)
        self.response.set_cookie(
            'session',
            session_token,
            flags=['HttpOnly', 'Secure']
            )
        result = self.HTTP_200()

        return result

class Logout(BaseHandler):
    """Route handler for logout requests."""
    @requires_login()
    def post(self):
        """POST /logout
        Deauthenticate the user making the request.
        """
        user = get_user_from_request(self.request)
        if user:
            logger.info(f'User {user.username} logged out.')
            self.response.delete_cookie('session')
            result = self.HTTP_200()

            return result
        else:
            result = self.HTTP_403(error='You are not logged in.')

            # Set csrf cookie
            self.set_csrf_cookie()
            return result

class Register(BaseHandler):
    """Route handler for registration requests."""

    @requires_params('email', 'username', 'password', 'password_confirm')
    def post(self):
        """POST /register
        Handle account registration.

        This step consists of:
            - checking that the email is valid
            - checking that the email is not already in use
            - checking that the username is not already in use
        """
        # First check that the email is validly formatted.
        email = self.request.data['email']
        if not validate_email(email):
            logger.warn(f'User attempted to register with an invalid email: {email}.')
            return self.HTTP_400(error='Email provided is not valid.')

        username = self.request.data['username']
        password = self.request.data['password']
        password_confirm = self.request.data['password_confirm']

        # Confirm that the passwords match.
        if not password == password_confirm:
            logger.info(f'Mismatched passwords while finishing regisrtation for user with email {email}.')
            return self.HTTP_400(error='Passwords do not match.')

        # Make sure that the username is not already taken.
        if username_taken(username):
            logger.info(f'User with email {email} attempted to create their account with an existing username, {username}.')
            return self.HTTP_400(error='Username already taken.')

        # Create the user.
        create_full_user(email, username, password)
        return self.HTTP_200()

class CurrentUser(BaseHandler):
    """Route handler for fetching the current user."""
    def get(self):
        """GET /current_user
        Fetch details and settings for the current user, as well as login status.
        """
        user = get_user_from_request(self.request)
        if not user:
            return self.HTTP_200(data={'logged_in': False, 'user': {}})
        user_data = {
            'username': user.username,
            'volume': user.volume,
        }
        return self.HTTP_200(data={'logged_in': True, 'user': user_data})

class SetUserVolume(BaseHandler):
    """Route handler for updating volume preferences."""
    @requires_login()
    @requires_params('volume')
    def post(self):
        """POST /set_volume

        Parameters:
            volume (str): String representation of the volume level setting to store.
        """
        user = get_user_from_request(self.request)

        # Set user volume
        set_user_volume(self.request)
        return self.HTTP_200()