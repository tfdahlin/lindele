
import logging, os, io
from wsgiref.util import FileWrapper

from pycnic.core import Handler
from pycnic.errors import HTTP_404

from PIL import Image

from music.util import refresh_database, get_all_tracks
from music.util import fetch_track_info, fetch_track_path, fetch_artwork_path, fetch_random_track_info

from util.util import BaseHandler

logger = logging.getLogger(__name__)
logging.basicConfig(level=logging.INFO)

class Songs(BaseHandler):
    def get(self, songid=None):
        if songid:
            try:
                data = fetch_track_info(int(songid))
            except:
                logger.warn(f'Could not fetch track information for song id {songid}')
                return self.failure()
            else:
                if data:
                    return self.success(data=data)
                raise HTTP_404('Track not found.')
        else:
            tracks = get_all_tracks()
            data = {
                'tracks': tracks
            }

        return self.success(data=data)

class RandomSong(BaseHandler):
    def get(self):
        try:
            data = fetch_random_track_info()
        except:
            logger.warn(f'Could not fetch random track.')
            return self.failure()
        else:
            if data:
                return self.success(data)
            raise HTTP_404('No songs found.')

class Audio(BaseHandler):
    def get(self, songid=None):
        if not songid:
            logger.warn('Request for audio made without a song id.')
            raise HTTP_404('Invalid song id.')

        try:
            track_file = fetch_track_path(int(songid))
        except:
            logger.warn(f'Could not fetch track audio for song id: {songid}.')
            raise HTTP_404('Invalid song id.')

        wrapper = FileWrapper(open(track_file, 'rb'))
        self.response.set_header('Content-Type', 'audio/mpeg')
        self.response.set_header('Content-Length', str(os.path.getsize(track_file)))
        self.response.set_header('Accept-Ranges', 'bytes')
        return wrapper

class Artwork(BaseHandler):
    def get(self, songid=None):
        if not songid:
            logger.warn('Request for artwork made without a song id.')
            raise HTTP_404('Invalid song id.')

        try:
            artwork_file = fetch_artwork_path(int(songid))
        except:
            logger.warn(f'Could not fetch track artwork for song id: {songid}.')
            raise HTTP_404('Invalid song id.')

        if artwork_file.endswith('.png'):
            self.response.set_header('Content-Type', 'image/png')
            with open(artwork_file, 'rb') as f:
                wrapper = FileWrapper(open(artwork_file, 'rb'))
                return wrapper
        elif artwork_file.endswith('.jpg'):
            self.response.set_header('Content-Type', 'image/jpeg')
            with open(artwork_file, 'rb') as f:
                wrapper = FileWrapper(open(artwork_file, 'rb'))
                return wrapper
        else:
            logger.warn(f'Error encountered while trying to fetch artwork for song with id {songid}.')
            raise HTTP_404('Album artwork not found.')

class BuildDatabase(BaseHandler):
    def get(self):
        refresh_database()
        return self.success()