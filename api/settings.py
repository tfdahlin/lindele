#!/usr/bin/env python
# -*- coding: utf-8 -*-
# Filename: settings.py
"""Base settings file.

Loads in local_settings, and makes adjustments accordingly.
"""

# Native python imports
import logging, os

# Local file imports
import local_settings

# PIP library imports
from sqlalchemy import create_engine

logger = logging.getLogger(__name__)
logging.basicConfig(level=logging.INFO)

# This section should give you an idea of what needs to be set in your local_settings.py file.

# String representation of the MAC address of the computer hosting the files
# e.g. "AA-AA-AA-AA-AA-AA"
MAGIC_PACKET_MAC_ADDRESS = None

# Does a file system need to be mounted?
NEED_TO_MOUNT = False
try:
    NEED_TO_MOUNT = local_settings.NEED_TO_MOUNT
except:
    logger.info('System does not need to mount media server.')

# Does the media server need to be woken up sometimes?
NEED_TO_WAKE = False
try:
    NEED_TO_WAKE = local_settings.NEED_TO_WAKE
except:
    logger.info('System does not need to wake media server.')

# Full path of the directory where music is stored
MUSIC_FOLDER = local_settings.MUSIC_FOLDER

# Path of the script that mounts the shared folder, if necessary
MOUNT_SHARE_SCRIPT = None
UNMOUNT_SHARE_SCRIPT = None

if NEED_TO_MOUNT:
    try:
        MOUNT_SHARE_SCRIPT = local_settings.MOUNT_SHARE_SCRIPT
    except Exception as e:
        logger.critical('ERROR: Mounting script cannot be found in local_settings file.')
        exit(1)

    try:
        UNMOUNT_SHARE_SCRIPT = local_settings.UNMOUNT_SHARE_SCRIPT
    except Exception as e:
        logger.critical('ERROR: Unmounting script cannot be found in local_settings file.')
        exit(1)

if NEED_TO_WAKE:
    try:
        MAGIC_PACKET_MAC_ADDRESS = local_settings.MAGIC_PACKET_MAC_ADDRESS
    except Exception as e:
        logger.critical('ERROR: MAC address for waking media server not specified in local_settings file.')

try:
    ALLOWED_ORIGINS = local_settings.ALLOWED_ORIGINS
except:
    logger.warn('ALLOWED_ORIGINS not specified in api/local_settings.py\n'
                'You will likely need to set this value in order to make cross-origin requests.\n'
                'This needs to be a list of strings.')
    ALLOWED_ORIGINS = [
        '127.0.0.1',
        'http://127.0.0.1'
    ]

BASE_PATH = os.path.dirname(os.path.abspath(__file__))
MISSING_ARTWORK_FILE = os.path.join(BASE_PATH, 'album_artwork_missing.png')

db_dialect = 'sqlite'

local_db_path = os.path.join(BASE_PATH, 'music_stream.db')
local_test_db_path = os.path.join(BASE_PATH, 'music_stream_test.db')

db_uri = f'sqlite:///{local_db_path}'
#test_db_uri = f'sqlite:///{local_test_db_path}'

# API version that's included with each response for clients.
API_VERSION = '1.0'

# Settings for storing hashed passwords.
hash_iterations=100000
hash_algo='sha256'