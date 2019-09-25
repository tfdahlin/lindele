
import logging, os
from wsgiref.util import FileWrapper

from pycnic.core import Handler
from pycnic.errors import HTTP_404

from music.util import refresh_database, get_all_tracks, fetch_track_info, fetch_track_path

from util.util import success

logger = logging.getLogger(__name__)
logging.basicConfig(level=logging.INFO)

class Songs(Handler):
    def get(self, songid=None):
        if songid:
            try:
                data = fetch_track_info(int(songid))
            except:
                logger.warn('Could not fetch track information.')
                return failure()
        else:
            tracks = get_all_tracks()
            data = {
                'tracks': tracks
            }
        return success(data=data)

class Audio(Handler):
    def get(self, songid=None):
        if not songid:
            raise HTTP_404('Invalid song id.')

        try:
            track_file = fetch_track_path(int(songid))
        except:
            logger.warn('Could not fetch track information.')
            raise HTTP_404('Could not ')

        wrapper = FileWrapper(open(track_file, 'rb'))
        self.response.set_header('Content-Type', 'audio/mpeg')
        self.response.set_header('Content-Length', str(os.path.getsize(track_file)))
        self.response.set_header('Accept-Ranges', 'bytes')
        return wrapper


class BuildDatabase(Handler):
    def get(self):
        refresh_database()
        return success()