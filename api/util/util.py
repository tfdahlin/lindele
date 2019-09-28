import shlex, os
from pathlib import Path
from subprocess import call
import settings

from pycnic.core import Handler

from settings import ALLOWED_ORIGINS

class BaseHandler(Handler):
    def before(self):
        origin = self.request.get_header('Origin')
        self.response.set_header('Vary', 'Origin')
        if origin in ALLOWED_ORIGINS:
            self.response.set_header('Access-Control-Allow-Origin', origin)

    def success(self, data={}, status=None, status_code=None, error=None):
        """Create default 200 response, following the format pycnic uses.

        Arguments:
            data (dict, optional): Data for response.
            status (str, optional): Status message for response.
            status_code (int, optional): Status code for response.
            error (str, optional): Error string for response (typically empty).

        Returns:
            result (dict): Data formatted for a json response.
        """
        if not status_code:
            status_code = 200
        if not status:
            status = f'{status_code} OK'
        if 'version' not in data:
            data['version'] = settings.API_VERSION
        result = {
            'status': status,
            'status_code': status_code,
            'data': data
        }

        if error:
            result['error'] = error

        return result

    def failure(self, data={}, status=None, status_code=None, error=None):
        """Create default 400 response, following the format pycnic uses.

        Arguments:
            data (dict, optional): Data for response.
            status (str, optional): Status message for response.
            status_code (int, optional): Status code for response.
            error (str, optional): Error string for response.

        Returns:
            result (dict): Data formatted for a json response.
        """
        if not status_code:
            status_code = 400
        if not status:
            status = f'{status_code} Failure'
        if 'version' not in data:
            data['version'] = settings.API_VERSION
        result = {
            'status': status,
            'status_code': status_code,
            'data': data,
            'error': error
        }

        return result

def reboot_machine():
    cmd = 'sudo systemctl reboot'
    os.system(cmd)


# A full mount script looks something like this:
"""
if grep -qs '/mnt/MountedFolder' /proc/mounts; then
    echo "Already mounted."
else
    if ! smbget -U user%password smb://ip.ad.dr.ess/folder | grep -q "is a directory"; then
        sudo mount -t cifs -v -o vers=3.0,username=my_username,password=my_password,ip=my_ip //MY_COMPUTER_NAME/folder /mnt/MountedFolder
    else
        echo "File not found."
    fi
fi
"""

def mount_as_needed(directory: str) -> bool:
    if is_mounted(directory):
        return True
    return mount_smb()

def is_mounted(directory: str) -> bool:
    from settings import MOUNTED_FOLDER

    p = Path(MOUNTED_FOLDER)
    return p.is_mount()

def mount_smb():
    """Mount the SMB drive specified in the local_settings file.

    Returns:
        success (bool): True if mounted successfully, false otherwise.
    """
    from settings import MOUNTING_USERNAME, MOUNTING_PASSWORD, MOUNTING_IP, MOUNTING_SHARE_NAME, MOUNTING_FOLDER, MUSIC_FOLDER

    if is_mounted(MUSIC_FOLDER):
        logger.info("Folder already mounted.")
        return False

    #smbget_cmd_array = [
    #    "!", "smbget", "-U",
    #    f"{MOUNTING_USERNAME}{MOUNTING_PASSWORD}",
    #    f"smb://{MOUNTING_IP}/{MOUNTING_FOLDER}",
    #    '|', 'grep', '-q',  '\"is a directory\"'
    #]
    #success = call(smbget_cmd_array, shell=True) == 0
    ##smbget_cmd = ' '.join(smbget_cmd_array)

    # mount the drive
    mount_cmd_array = [
        'sudo', 'mount', '-t',
        'cifs', '-v', '-o',
        f'vers=3.0,username={MOUNTING_USERNAME},password={MOUNTING_PASSWORD},ip={MOUNTING_IP}',
        MOUNTING_SHARE_NAME, MOUNTED_FOLDER
    ]
    success = call(mount_cmd_array, shell=True) == 0
    return success

