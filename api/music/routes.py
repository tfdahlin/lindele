
import logging, os, io
from wsgiref.util import FileWrapper

from pycnic.core import Handler
from pycnic.errors import HTTP_404, HTTP_401

from PIL import Image

from music.util import create_new_playlist, get_playlist_data_from_id, owns_playlist
from music.util import get_public_playlists, get_playlists_for_user
from music.util import add_song_to_playlist, remove_song_from_playlist
from music.util import refresh_database, get_all_tracks, get_playlists_owned_by_user
from music.util import fetch_track_info, fetch_track_path, fetch_artwork_path, fetch_random_track_info
from music.models import Playlist
from music.models import Song

from users.util import get_user_from_request, is_logged_in

from util.decorators import requires_params, requires_login
from util.util import BaseHandler, mount_as_needed

logger = logging.getLogger(__name__)
logging.basicConfig(level=logging.INFO)

class Songs(BaseHandler):
    def get(self, songid=None):
        mount_as_needed()
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

class Playlists(BaseHandler):
    def get(self, playlistid=None):
        if is_logged_in(self.request):
            user = get_user_from_request(self.request)
        else:
            user = None

        if not playlistid:
            # Get public playlists, and any that belong to user
            if user:
                accessible_playlists = get_playlists_for_user(user.guid)
            else:
                accessible_playlists = get_public_playlists()
            return self.success(data=accessible_playlists)
        else:
            # Fetch a specific playlist
            playlist_data = get_playlist_data_from_id(playlistid)
            if playlist_data['public'] or (user and owns_playlist(playlistid, user.guid)):
                del(playlist_data['public'])
                return self.success(data=playlist_data)
            else:
                raise HTTP_401('You cannot access this playlist.')

            # Check if the user can access the playlist.

class OwnedPlaylists(BaseHandler):
    def get(self):
        if is_logged_in(self.request):
            user = get_user_from_request(self.request)
        else:
            return self.success(data={'playlists': []})
        return self.success(data=get_playlists_owned_by_user(user.guid))

class CreatePlaylist(BaseHandler):
    @requires_login()
    @requires_params('playlist_name')
    def post(self):
        user = get_user_from_request(self.request)
        playlist_name = self.request.data['playlist_name']
        create_new_playlist(playlist_name, user.guid, user.username)
        logger.info(f"User {user.username} created new playlist: {playlist_name}")
        return self.success(data={'msg': f'Playlist {playlist_name} successfully created.'})

class AddToPlaylist(BaseHandler):
    @requires_login()
    @requires_params('songid')
    def post(self, playlistid):
        user = get_user_from_request(self.request)
        if not owns_playlist(playlistid, user.guid):
            raise HTTP_401('You don\'t own this playlist!')

        songid = self.request.data['songid']
        add_song_to_playlist(playlistid, songid)
        # TODO: Add song to playlist
        return self.success(data={'msg': f'success'})

class RemoveFromPlaylist(BaseHandler):
    @requires_login()
    @requires_params('songid')
    def post(self, playlistid):
        user = get_user_from_request(self.request)
        if not owns_playlist(playlistid, user.guid):
            raise HTTP_401('You don\'t own this playlist!')

        songid = self.request.data['songid']
        remove_song_from_playlist(playlistid, songid)
        # TODO: Remove song from playlist.
        return self.success(data={'msg': f'success'})