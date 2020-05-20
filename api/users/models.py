#!/usr/bin/env python
# -*- coding: utf-8 -*-
# Filename: users/models.py
"""Model classes for user-related database objects."""

# Native python imports

# Local file imports
from util.models import Base, GUID, HexByteString

# PIP library imports
import sqlalchemy
from sqlalchemy import create_engine
from sqlalchemy import Column, Integer, String, DateTime, Boolean
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship
from sqlalchemy_utils import IPAddressType

class LoginAttempt(Base):
    """Model used for tracking login attempts.

    Attributes:
        __tablename__ (str): Name of the database table.
        id (int): Primary key for the table.
        email (str): Email address that is attempting to login.
        attempt_time (datetime): Time of login attempt.
        source_ip (str): IP of the user attempting to login
        success (bool): Whether the login attempt was successful or not.
    """

    __tablename__ = 'login_attempts'

    id = Column(Integer, primary_key=True)
    email = Column(String)
    attempt_time = Column(DateTime)
    source_ip = Column(IPAddressType)
    success = Column(Boolean)

class User(Base):
    """User account model stored in database and used for authentication.

    Attributes:
        __tablename__ (str): Name of the database table.
        username (str): Username of the user
        email (str): Email of the user.
        password_hash (str): String containing the hash of the user, 
            as well as information about how the hash was generated.
        guid (uuid): UUID and primary key for the user.
        last_registration_email (datetime): Last time that an attempt was made to send a user an email.
        last_invalidated (datetime): Last time that session tokens were invalidated.
    """

    __tablename__ = 'user'

    username = Column(String)
    email = Column(String)
    password_hash = Column(String)
    guid = Column(GUID, primary_key=True, nullable=False)
    volume = Column(Integer, default=100, nullable=False)
    admin = Column(Boolean, default=False)

    last_registration_email = Column(DateTime)

    last_invalidated = Column(DateTime)

    def __repr__(self):
        """Override user representation."""
        return f'<User(username={self.username}, email={self.email})>'