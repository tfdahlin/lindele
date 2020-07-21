#!/usr/bin/env python
# -*- coding: utf-8 -*-
# Filename: util/util.py
"""Utility functions and classes for all modules."""

# Native python imports
import shlex, os, time
from pathlib import Path
from subprocess import call
import subprocess

# Local file imports
import local_settings
import settings
from settings import *

# PIP library imports
from pycnic.core import Handler
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from wakeonlan import send_magic_packet

# Variables and settings
engine = create_engine(db_uri)
Session = sessionmaker(bind=engine)

class RangeFileWrapper:
    """FileWrapper with support for byte ranges.

    Borrowed from https://gist.github.com/dcwatson/cb5d8157a8fa5a4a046e"""

    def __init__(self, filelike, blksize=8192, offset=0, length=None):
        """Initialization function for iterable wrapper."""
        self.filelike = filelike
        self.filelike.seek(offset, os.SEEK_SET)
        self.remaining = length
        self.blksize = blksize

    def close(self):
        """Closes filelike."""
        if hasattr(self.filelike, 'close'):
            self.filelike.close()

    def __iter__(self):
        """Returns self as iterator."""
        return self

    def __next__(self):
        """Fetches next set of readable bytes."""
        if self.remaining is None:
            # If remaining is None, we're reading the entire file.
            data = self.filelike.read(self.blksize)
            if data:
                return data
            raise StopIteration()
        else:
            if self.remaining <= 0:
                raise StopIteration()
            data = self.filelike.read(min(self.remaining, self.blksize))
            if not data:
                raise StopIteration()
            self.remaining -= len(data)
            return data

class BaseHandler(Handler):
    """Extension of pycnic's Handler class. 

    Provides utility functions for inheriting in specific http response handlers.
    """
    def before(self):
        """Executes on receiving a request before any other execution.
        This sets necessary headers.
        """
        origin = self.request.get_header('Origin')
        self.response.set_header('Vary', 'Origin')
        if origin in ALLOWED_ORIGINS:
            self.response.set_header('Access-Control-Allow-Origin', origin)
            self.response.set_header('Access-Control-Allow-Credentials', "true")
        self.response.set_header('X-Robots-Tag', 'noindex, nofollow, noarchive, notranslate, noimageindex')

    def HTTP_200(self, data={}, error=None): # 200 OK -- general success
        """200 OK response.

        General success

        Arguments:
            data (dict): Data to be returned in the response.
            error (str): Any error message that wants to be added to the response.
        """
        result = {
            'status_code': 200,
            'status': 'OK',
            'version': settings.API_VERSION,
            'data': data,
            'error': error
        }
        self.response.status_code = 200
        return result

    def HTTP_201(self, data={}, error=None):
        """201 Created response.

        Resource has been created.

        Arguments:
            data (dict): Data to be returned in the response.
            error (str): Any error message that wants to be added to the response.
        """
        result = {
            'status_code': 201,
            'status': 'Created',
            'version': settings.API_VERSION,
            'data': data,
            'error': error
        }
        self.response.status_code = 201
        return result

    def HTTP_400(self, data={}, error=None): # 400 Bad Request -- request not understood by server
        """400 Bad Request response.

        Request not understood by server, general failure.

        Arguments:
            data (dict): Data to be returned in the response.
            error (str): Any error message that wants to be added to the response.
        """
        result = {
            'status_code': 400,
            'status': 'Bad Request',
            'version': settings.API_VERSION,
            'data': data,
            'error': error
        }
        self.response.status_code = 400
        return result

    def HTTP_403(self, data={}, error=None): # 403 Forbidden -- no permission
        """403 Forbidden response.

        User does not have permission to access the resource

        Arguments:
            data (dict): Data to be returned in the response.
            error (str): Any error message that wants to be added to the response.
        """
        result = {
            'status_code': 403,
            'status': 'Forbidden',
            'version': settings.API_VERSION,
            'data': data,
            'error': error
        }
        self.response.status_code = 403
        return result

    def HTTP_404(self, data={}, error=None): # 404 Not Found -- resource not found
        """404 Not Found response.

        Resource not found

        Arguments:
            data (dict): Data to be returned in the response.
            error (str): Any error message that wants to be added to the response.
        """
        result = {
            'status_code': 404,
            'status': 'Not Found',
            'version': settings.API_VERSION,
            'data': data,
            'error': error
        }
        self.response.status_code = 404
        return result

    def HTTP_416(self, data={}, error=None): # 416 Requested Range Not Satisfiable -- out of bounds request
        """416 Requested Range Not Satisfiable response.

        Range requested was out of allowed bounds, e.g. "start" was beyond filesize.

        Arguments:
            data (dict): Data to be returned in the response.
            error (str): Any error message that wants to be added to the response.
        """
        result = {
            'status_code': 416,
            'status': 'Requested Range Not Satisfiable',
            'version': settings.API_VERSION,
            'data': data,
            'error': error
        }
        self.response.status_code = 429
        return result

    def HTTP_429(self, data={}, error=None): # 429 Too Many Requests -- rate-limiting
        """429 Too Many Requests response.

        Rate limiting applied

        Arguments:
            data (dict): Data to be returned in the response.
            error (str): Any error message that wants to be added to the response.
        """
        result = {
            'status_code': 429,
            'status': 'Too Many Requests',
            'version': settings.API_VERSION,
            'data': data,
            'error': error
        }
        self.response.status_code = 429
        return result

class access_db:
    """Wrapper class to use when accessing the database.

    This automatically closes database connections on completion, 
    and is designed solely for convenience.

    Example:
    with access_db() as db_conn:
        do_stuff()
        db_conn.commit()
    """
    def __enter__(self):
        """Connects to the database and return the connection as part of the setup process."""
        self.db_conn = Session()
        return self.db_conn

    def __exit__(self, type, value, traceback):
        """Closes the database connection as part of the teardown process."""
        self.db_conn.close()

def reboot_machine_with_delay():
    """Reboot the server after 30 seconds."""
    time.sleep(30)
    reboot_machine()

def reboot_machine():
    """Reboot the server."""
    cmd = 'sudo systemctl reboot'
    os.system(cmd)



def mount_as_needed():
    """Wake the media server, then mount if necessary."""
    wake_media_server()
    try:
        is_mounted()
    except OSError as e:
        # Sometimes, a mount fails in a weird way. This attempts to fix that.
        if e.strerror == 'Host is down':
            # unmount folder
            logger.warn(f'Samba connection failed. Attempting to unmount {MUSIC_FOLDER}.')
            unmount_smb()
        else:
            logger.critical('Error while checking mount.')
            logger.critical(e)
            raise e
    else:
        return

    logger.warn('Remounting media server.')
    mount_smb()

def is_mounted() -> bool:
    """Check if the media server is mounted or not."""
    # If we don't need to mount, pretend it's mounted.
    if not settings.NEED_TO_MOUNT:
        return True

    wake_media_server()
    p = Path(MUSIC_FOLDER)
    result = p.is_mount()
    return result

def unmount_smb():
    """Unmount the music directory, if necessary."""
    # If we don't need to mount, skip this.
    if not settings.NEED_TO_MOUNT:
        return

    os.system(f'sudo {settings.UNMOUNT_SHARE_SCRIPT}')

def mount_smb():
    """Mount the SMB drive specified in the local_settings file, if necessary.

    The mounting script should look something like this:
    sudo mount -t cifs -v -o vers=3.0,username=media_server_username,password=media_server_password,ip=media_server_ip //media_server_name/folder /mnt/LocalMountedFolder
    e.g.:
    sudo mount -t cifs -v -o vers=3.0,username=foo,password=bar,ip=192.168.1.100 //MUSIC_SERVER/Music /mnt/Music
    """
    # If we don't need to mount, skip this.
    if not settings.NEED_TO_MOUNT:
        return

    wake_media_server()

    os.system(f'sudo {settings.MOUNT_SHARE_SCRIPT}')

def wake_media_server():
    """Wake the media server by sending it a magic packet."""
    if settings.NEED_TO_WAKE:
        send_magic_packet(local_settings.MAGIC_PACKET_MAC_ADDRESS)