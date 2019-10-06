import threading, logging

from wakeonlan import send_magic_packet

import local_settings

from users.util import get_user_from_request, is_logged_in

from util.decorators import requires_params, requires_login
from util.util import BaseHandler, reboot_machine_with_delay, mount_as_needed, wake_media_server

logger = logging.getLogger(__name__)
logging.basicConfig(level=logging.INFO)

class Restart(BaseHandler):
    @requires_login()
    def get(self):
        logger.warn('Restarting server.')
        wake_media_server()
        t = threading.Thread(target=reboot_machine_with_delay)
        t.start()
        return self.success()

class Remount(BaseHandler):
    @requires_login()
    def get(self):
        logger.warn('Remounting media server.')
        wake_media_server()
        mount_as_needed()
        return self.success()