#!/usr/bin/env python
# -*- coding: utf-8 -*-
# Filename: users/models.py
"""Models file for users.

This file contains the models used for storing information about users in the database.

Classes:
    User: Main model used for authentication of a user.
"""
import sqlalchemy
from sqlalchemy import create_engine
from sqlalchemy import Column, Integer, String, DateTime, Boolean
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship

from sqlalchemy_utils import IPAddressType

from settings import engine

from util.models import GUID, HexByteString

Base = declarative_base()

class LoginAttempt(Base):
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
    volume = Column(Integer)

    last_registration_email = Column(DateTime)

    last_invalidated = Column(DateTime)

    def __repr__(self):
        return f'<User(username={self.username}, email={self.email})>'

Base.metadata.create_all(engine)