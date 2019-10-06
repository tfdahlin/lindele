from sqlalchemy import create_engine

try:
    import local_settings
except Exception as e:
    print("Unable to import local_settings file.")
    raise e

import logging, os

logger = logging.getLogger(__name__)
logging.basicConfig(level=logging.INFO)

debug_sql_output = False

failures = 0

# This section should give you an idea of what needs to be set in your local_settings.py file.

# The MAC address of the computer hosting the files
MAGIC_PACKET_MAC_ADDRESS = "AA-AA-AA-AA-AA-AA"

# Does a file system need to be mounted?
NEED_TO_MOUNT = False

# If the file system needs to be mounted, then these options need to be set.
MOUNTING_USERNAME = None
MOUNTING_PASSWORD = None
MOUNTING_IP = None # Ip address of device to connect to
MOUNTED_SHARE_NAME = None # SMB share name (e.g. //PERSONAL_COMPUTER/music)
MOUNTED_FOLDER = None # Name of folder on native system to mount to (e.g. /mnt/Music)
MOUNTING_FOLDER = None # Name of folder on foreign system to mount (e.g. )
MUSIC_FOLDER = None

try:
    # Where you store your music e.g. '/home/music/tracks', unless mounting a filesystem
    MUSIC_FOLDER = local_settings.MUSIC_FOLDER
except:
    logger.info("MUSIC_FOLDER not specified in api/local_settings.py")
    try:
        # Where your music folder is mounted e.g. '/mnt/music'
        MOUNTED_FOLDER = local_settings.MOUNTED_FOLDER
        MOUNT_SHARE_SCRIPT = local_settings.MOUNT_SHARE_SCRIPT
    except:
        logger.critical("ERROR: Neither MUSIC_FOLDER nor MOUNTED_FOLDER are set in api/local_settings.py")
        exit(1)
    else:
        # We only care about the magic packet mac address if the music is being mounted.
        try:
            # The MAC address of the device hosting the music folder.
            MAGIC_PACKET_MAC_ADDRESS = local_settings.MAGIC_PACKET_MAC_ADDRESS
        except:
            logger.info("MAGIC_PACKET_MAC_ADDRESS not set in api/local_settings.py\n"
                        "If you are not using wakeonlan, this can be safely ignored.")
            MAGIC_PACKET_MAC_ADDRESS = None
else:
    MAGIC_PACKET_MAC_ADDRESS = None

try:
    ALLOWED_ORIGINS = local_settings.ALLOWED_ORIGINS
except:
    logger.info('ALLOWED_ORIGINS not specified in api/local_settings.py\n'
                'You likely need to set this value in order to make cross-origin requests.')
    ALLOWED_ORIGINS = []

if not MUSIC_FOLDER:
    MUSIC_FOLDER = MOUNTED_FOLDER
if not MOUNTED_FOLDER:
    MOUNTED_FOLDER = MUSIC_FOLDER

BASE_PATH = os.path.dirname(os.path.abspath(__file__))
MISSING_ARTWORK_FILE = os.path.join(BASE_PATH, 'album_artwork_missing.png')

db_dialect = 'sqlite'
#db_username = 'foo'
#db_password = 'bar'
#hostname = 'localhost'

local_db_path = os.path.join(BASE_PATH, 'music_stream.db')
local_test_db_path = os.path.join(BASE_PATH, 'music_stream_test.db')

db_uri = f'{db_dialect}:///{local_db_path}'
test_db_uri = f'{db_dialect}:///{local_test_db_path}'

API_VERSION = '1.0'


engine = create_engine(db_uri, echo=debug_sql_output)

hash_iterations=100000
hash_algo='sha256'