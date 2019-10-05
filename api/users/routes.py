#!/usr/bin/env python
# -*- coding: utf-8 -*-
# Filename: users/routes.py
"""Routes file for users.

This file manages all the routing for user functions.

Classes:
    UsersRoutes: Handles requests to /users/<username>.
    Login: Handles requests to /login.
    Logout: Handles requests to /logout.
    Register: Handles requests to /register.
"""

import hashlib, secrets, binascii, logging, uuid, ipaddress, datetime

from pycnic.core import Handler
from pycnic.errors import HTTP_404

from sqlalchemy.orm import sessionmaker

from settings import hash_iterations

from util.decorators import requires_params, requires_login
from util.util import BaseHandler

from users.models import User, engine
from users.util import *

logger = logging.getLogger(__name__)
logging.basicConfig(level=logging.INFO)

class UsersRoutes(BaseHandler):
    """Handler for requests to /users/<username>"""
    def get(self, username=None):
        """Load user info. Currently only echoes the username if the user exists."""
        user = fetch_user_by_username(username)
        if not user:
            raise HTTP_404('User not found.')
        # TODO: Figure out what we return when a user's page is accessed.
        # TODO: More information in docstring.
        return self.success({'username': username})

class Login(BaseHandler):
    """Handle account login."""
    @requires_params('email', 'password')
    def post(self):
        """Attempt to authenticate a user."""
        # TODO: better docstring
        email = self.request.data['email']
        input_password = self.request.data['password']
        ip = ipaddress.ip_address(self.request.ip)

        user = fetch_user_by_email(email)

        if login_attempts_exceeded(email):
           logger.warn(f'User with email {email} tried to login too many times. Rate limiting applied.')
           return self.failure({'msg': 'Too many failed login attempts. Please try again later.'})

        if not user:
            logger.warn(f'Tried to log in with email {email}, but this email is not registered.')
            log_login_attempt(email, False, ip)
            return self.failure(error='Login failed.', status_code=401)

        if not user.password_hash:
            logger.warn(f'Tried to log in with email {email}, but this account has not completed registration.')
            log_login_attempt(email, False, ip)
            return self.failure(error='Login failed.', status_code=401)

        if not check_password(input_password, user.password_hash):
            log_login_attempt(email, False, ip)
            logger.warn(f'Tried to log in with email {email}, but input password did not match stored password.')
            return self.failure(error='Login failed.', status_code=401)

        logger.info(f'User {user.username} logged in.')
        log_login_attempt(email, True, ip)

        # Generate a session token for the user, and set their session cookie.
        session_token = create_session_token(user)
        self.response.set_cookie(
            'session',
            session_token,
            flags=['HttpOnly', 'Secure']
            )
        result = self.success({'msg': 'Logged in successfully'})

        return result

class Logout(BaseHandler):
    """Handle account logout."""
    @requires_login()
    def post(self):
        """Deauthenticate the user making the request."""
        user = get_user_from_request(self.request)
        if user:
            logger.info(f'User {user.username} logged out.')
            self.response.delete_cookie('session')
            result = self.success({'msg': 'Logged out successfully.'})

            return result
        else:
            result = self.failure(error='You are not logged in.')

            # Set csrf cookie
            self.set_csrf_cookie()
            return result

class Register(BaseHandler):
    """Handle account registration."""

    @requires_params('email', 'username', 'password', 'password_confirm')
    def post(self, uuid=None):
        """Handle account registration.

        This step consists of:
            - checking that the email is valid
            - checking that the email is not already in use
            - checking that the username is not already in use
        """
        email = self.request.data['email']
        if not validate_email(email):
            logger.warn(f'User attempted to register with an invalid email: {email}.')
            return self.failure(error='Email provided is not valid.')

        if rate_limited_email(email):
            logger.warn(f'Attempted to exceed rate limit for emails to {email}.')
            return self.success()


        username = self.request.data['username']
        password = self.request.data['password']
        password_confirm = self.request.data['password_confirm']

        # Confirm that the passwords match.
        if not password == password_confirm:
            logger.info(f'Mismatched passwords while finishing regisrtation for user with email {email}.')
            return self.failure(error='Passwords do not match.')
        
        if username_taken(username):
            logger.info(f'User with email {email} attempted to create their account with an existing username, {username}.')
            return self.failure(error='Username already taken.')

        create_full_user(email, username, password)

        return self.success(status='Registration completed.')

class CurrentUser(BaseHandler):
    def get(self):
        user = get_user_from_request(self.request)
        if not user:
            return self.success(data={'logged_in': False, 'user': {}})
        user_data = {
            'username': user.username,
        }
        return self.success(data={'logged_in': True, 'user': user_data})
        pass