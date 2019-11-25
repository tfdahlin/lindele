#!/usr/bin/env python
# -*- coding: utf-8 -*-
# Filename: util/routes.py

# Native python imports
import threading, logging

# Local file imports
import local_settings
from users.util import get_user_from_request, is_logged_in
from util.decorators import requires_params, requires_login
from util.util import BaseHandler, reboot_machine_with_delay, mount_as_needed, wake_media_server

# PIP library imports
from wakeonlan import send_magic_packet

# Variables and settings
logger = logging.getLogger(__name__)
logging.basicConfig(level=logging.INFO)

class Restart(BaseHandler):
    """Route handler for restarting the music player server."""
    @requires_login()
    def get(self):
        """GET /restart

        Restarts the server hosting the music player."""
        logger.warn('Restarting server.')
        wake_media_server()
        t = threading.Thread(target=reboot_machine_with_delay)
        t.start()
        return self.HTTP_200()

class Remount(BaseHandler):
    """Route handler for restarting the media server."""
    @requires_login()
    def get(self):
        """GET /remount

        Wakes the media server and mounts as necessary."""
        wake_media_server()
        mount_as_needed()
        return self.HTTP_200()