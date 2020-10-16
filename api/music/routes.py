#!/usr/bin/env python
# -*- coding: utf-8 -*-
# Filename: music/routes.py
"""Route handlers related to music database objects."""

# Native python imports
import logging, os, io, re, json, gzip
from wsgiref.util import FileWrapper

# Local code imports
import users.util, music.util
from util.decorators import requires_params, requires_login, requires_admin
from util.util import BaseHandler, mount_as_needed, RangeFileWrapper
from settings import MISSING_ARTWORK_FILE, local_db_path

# PIP library imports
from pycnic.core import Handler
from PIL import Image

# Variables and config
logger = logging.getLogger(__name__)
logging.basicConfig(level=logging.INFO)

class Songs(BaseHandler):
    """Route handler for fetching track information."""

    def get(self, songid=None):
        """GET /songs/[songid].

        Arguments:
            songid (str): Integer string identifying that info about a single song should be fetched.
        """
        # Reading information from the database will be faster than processing
        # a list of all songs, so if a specific songid is requested, we use a
        # database lookup.
        if songid:
            # If a song id is specified, fetch info about that track specifically.
            try:
                data = music.util.fetch_track_info(int(songid))
            except:
                logger.warn(f'Could not fetch track information for song id {songid}')
                return self.HTTP_400()
            else:
                if data:
                    return self.HTTP_200(data=data)
                return self.HTTP_404()

        music_dir = os.path.dirname(os.path.abspath(__file__))
        cache_dir = os.path.join(music_dir, 'cache_files')
        songs_cache = os.path.join(cache_dir, 'songs.cache')
        gzip_songs_cache = os.path.join(cache_dir, 'songs.cache.gz')

        # Check if the cache file exists, and if so, load it if it's fresher
        #  than the database file.
        if os.path.exists(cache_dir):
            # Check for gzip cache and support for gzip in request
            if ('Accept-Encoding' in self.request.headers and
                'gzip' in self.request.headers['Accept-Encoding'].lower() and
                os.path.exists(gzip_songs_cache)):
                    songs_cache_age = os.path.getmtime(gzip_songs_cache)
                    db_file_age = os.path.getmtime(local_db_path)
                    if songs_cache_age > db_file_age:
                        self.response.status_code = 200
                        self.response.set_header('Content-Encoding', 'gzip')
                        wrapper = FileWrapper(open(gzip_songs_cache, 'rb'))
                        return wrapper
            # If those requirements aren't met, return uncompressed cache when possible
            elif os.path.exists(songs_cache):
                songs_cache_age = os.path.getmtime(songs_cache)
                db_file_age = os.path.getmtime(local_db_path)
                if songs_cache_age > db_file_age:
                    with open(songs_cache, 'r') as f:
                        data = json.loads(f.read())
                        return self.HTTP_200(data=data)

        else:
            # If the cache directory does not exist, make it.
            os.mkdir(cache_dir)

        # By this point, the cache lookup has failed, so we get all tracks from
        # the database, save the result to file, then return the result.
        tracks = music.util.get_all_tracks()
        data = {
            'tracks': tracks
        }

        # Write uncompressed cache
        with open(songs_cache, 'w') as f:
            f.write(json.dumps(data))
        # Write compressed cache
        with gzip.open(gzip_songs_cache, 'wb') as f:
            f.write(json.dumps(self.HTTP_200(data=data)).encode())

        if ('Accept-Encoding' in self.request.headers and
            'gzip' in self.request.headers['Accept-Encoding'].lower()):
            self.response.set_header('Content-Encoding', 'gzip')
            self.response.status_code = 200
            wrapper = FileWrapper(open(gzip_songs_cache, 'rb'))
            return wrapper
        else:
            return self.HTTP_200(data=data)

class Audio(BaseHandler):
    """Route handler for fetching track audio files."""

    def get(self, songid):
        """GET /songs/<songid>/audio.

        Arguments:
            songid (str): Integer string identifying the track that should be served.
        """
        try:
            track_file = music.util.fetch_track_path(int(songid))
            track_hash = music.util.fetch_track_hash(int(songid))
        except:
            logger.warn(f'Could not fetch track audio for song id: {songid}.')
            return self.HTTP_404(error='Invalid song id.')

        # Log which users listen to which songs.
        try:
            track_info = music.util.fetch_track_info(int(songid))
        except:
            logger.warn(f'Could not fetch track info for song id: {songid}.')
        else:
            if music.util.check_file_missing(int(songid)):
                logger.warn(f'File for songid {songid} missing.')
                return self.HTTP_400(error='Could not load track.')
            user = None
            if users.util.is_logged_in(self.request):
                user = users.util.get_user_from_request(self.request)
                user = user.username
            else:
                user = 'Anonymous user'
            if track_info:
                logger.info(f'{user} is listening to {track_info["title"]} by {track_info["artist"]}')

        download_filename = track_info['title'] + '.mp3'

        # Remove .mp3 and replace with .flac, then check if file exists
        if 'flac' in self.request.args:
            flac_track_file = f'{track_file[:-4]}.flac'
            print(f'Flac file: {flac_track_file}')
            if os.path.exists(flac_track_file):
                track_file = flac_track_file
                download_filename = download_filename[:-4] + '.flac'

        # Only mount if we actually need to load the file.
        # This is specifically for my setup where the media server may go to sleep
        #  and is separate from the main server, so it may need to be mounted before
        #  tracks can be opened.
        mount_as_needed()

        # Used for parsing range requests
        range_re = re.compile(r'bytes\s*=\s*(\d+)\s*-\s*(\d*)', re.I)

        # Regardless of range, we need to know file size
        file_size = os.path.getsize(track_file)

        # These will be different depending on the range requested
        content_length = None
        wrapper = None

        if 'Range' in self.request.headers and range_re.match(self.request.headers['Range']):
            # If a range is requested, we use the RangeFileWrapper to only serve the range requested
            # TODO: add if-range (hash of file, should be part of audio track model)
            # https://developer.mozilla.org/en-US/docs/Web/HTTP/Range_requests#Partial_request_responses
            range_match = range_re.match(self.request.headers['Range'])
            first_byte, last_byte = range_match.groups()
            if int(first_byte) > file_size:
                # Out of bounds request, return an error
                return self.HTTP_416(error='Requested range out of bounds.')
            first_byte = int(first_byte) if first_byte else 0
            last_byte = int(last_byte) if last_byte else file_size - 1
            if last_byte >= file_size:
                last_byte = file_size - 1
            length = last_byte - first_byte + 1
            wrapper = RangeFileWrapper(open(track_file, 'rb'), offset=first_byte, length=length)
            content_length = str(length)
            if 'dl' in self.request.args and self.request.args['dl'] == '1':
                self.response.set_header('Content-Disposition', f'attachment; filename="{download_filename}"')
            self.response.set_header('Content-Range', f'bytes {first_byte}-{last_byte}/{file_size}')
            self.response.set_header('If-Range', f'"{track_hash}"')
            self.response.status_code = 206

        else:
            # If no range is requested, we serve the whole file
            content_length = str(file_size)
            try:
                wrapper = FileWrapper(open(track_file, 'rb'))
            except OSError as e:
                logger.warn(f'Exception while loading track {songid}.')
                return self.HTTP_400(error='Could not load track.')

        if 'dl' in self.request.args and self.request.args['dl'] == '1':
            self.response.set_header('Content-Disposition', f'attachment; filename="{download_filename}"')
        if download_filename.endswith('mp3'):
            self.response.set_header('Content-Type', 'audio/mpeg')
        elif download_filename.endswith('flac'):
            self.response.set_header('Content-Type', 'audio/flac')

        self.response.set_header('Content-Length', content_length)
        self.response.set_header('Accept-Ranges', 'bytes')
        return wrapper

class Artwork(BaseHandler):
    """Route handler for fetching track artwork files."""

    def get(self, songid):
        """GET /songs/<songid>/artwork.

        Arguments:
            songid (str): Integer string identifying the track that should have its artwork served.
        """
        mount_as_needed()
        try:
            artwork_file = music.util.fetch_artwork_path(int(songid))
        except:
            logger.warn(f'Could not fetch track artwork for song id: {songid}.')
            return self.HTTP_404(error='Invalid song id.')

        try:
            content_type = self.get_content_type(artwork_file)
        except:
            return self.HTTP_400(error='Error determining album artwork content type.')

        # File size is constant.
        file_size = os.path.getsize(artwork_file)

        try:
            wrapper = self.get_wrapper(artwork_file)
        except Exception as e:
            logger.warn(f'Could not access artwork file for track with id {songid}, or missing album artwork.')
            logger.critical(e)
            return self.HTTP_400(error='Error loading album artwork.')
        else:
            self.response.set_header('Content-Length', str(file_size))
            self.response.set_header('Content-Type', content_type)
            return wrapper

    def get_content_type(self, filename):
        """Returns the content-type string for a given filename."""
        if filename.endswith('.png'):
            return 'image/png'
        elif filename.endswith('.jpg') or filename.endswith('.jpeg'):
            return 'image/jpeg'
        else:
            raise TypeError(f'File type could not be determined for {filename}')

    def get_wrapper(self, filename, error=False):
        """Create wrapper for file, then return the wrapper, content-type, and file size."""
        wrapper = None
        try:
            wrapper = FileWrapper(open(filename, 'rb'))
        except OSError as e:
            logger.warn(f'Could not access artwork file: {filename}.')
            logger.info(f'Attempting to load {MISSING_ARTWORK_FILE} instead.')
            if error:
                raise e
            else:
                return get_wrapper(MISSING_ARTWORK_FILE, error=True)
        else:
            return wrapper

class BuildDatabase(BaseHandler):
    """Route handler for building/refreshing the track database."""

    @requires_admin()
    def get(self):
        """GET /refresh."""
        # Asynchronous thread that refreshes the database, so the user doesn't have to wait.
        music.util.refresh_database()
        # Return success immediately
        return self.HTTP_200()

class Playlists(BaseHandler):
    """Route handler for fetching playlist information."""

    def get(self, playlistid=None):
        """GET /playlists/[playlistid].

        Arguments:
            playlistid (str): Integer string identifying a unique playlist.
        """
        if users.util.is_logged_in(self.request):
            user = users.util.get_user_from_request(self.request)
        else:
            user = None

        if not playlistid:
            return self.fetch_available_playlists(user)
        else:
            # Fetch a specific playlist
            return self.fetch_unique_playlist(user, playlistid)

    def fetch_available_playlists(self, user):
        """Fetch playlists that are available to a specific user.
        
        This includes public playlists, and playlists created by the user.

        Arguments:
            user (User): The user we are fetching playlists for, or None.
        """
        if user:
            accessible_playlists = music.util.get_playlists_for_user(user.guid)
        else:
            accessible_playlists = music.util.get_public_playlists()
        return self.HTTP_200(data=accessible_playlists)
            
    def fetch_unique_playlist(self, user, playlistid):
        """Fetch a playlist identified by a unique playlistid.

        Arguments:
            user (User): The user we are fetching the playlist for, or None.
            playlistid (str): Integer string identifying the requests playlist.
        """
        playlist_data = music.util.get_playlist_data_from_id(playlistid)
        if not playlist_data:
            return self.HTTP_404()

        # We only want to return the playlist data if it's public, or owned by the user.
        if playlist_data['public'] or (user and music.util.owns_playlist(playlistid, user.guid)):
            return self.HTTP_200(data=playlist_data)
        else:
            return self.HTTP_403(error='You cannot access this playlist.')

class OwnedPlaylists(BaseHandler):
    """Route handler for fetching owned playlists."""

    @requires_login()
    def get(self):
        """GET /playlists/owned."""
        if users.util.is_logged_in(self.request):
            user = users.util.get_user_from_request(self.request)
        else:
            return self.HTTP_200(data={'playlists': []})
        owned_playlists = music.util.get_playlists_owned_by_user(user.guid)
        return self.HTTP_200(data=owned_playlists)

class CreatePlaylist(BaseHandler):
    """Route handler for creating playlists."""

    @requires_login()
    @requires_params('playlist_name')
    def post(self):
        """POST /playlists/create.

        Parameters:
            playlist_name (str): The name to be given to the playlist.
        """
        user = users.util.get_user_from_request(self.request)
        playlist_name = self.request.data['playlist_name']

        music.util.create_new_playlist(playlist_name, user.guid, user.username)

        logger.info(f"User {user.username} created new playlist: {playlist_name}")
        return self.HTTP_200()

class AddToPlaylist(BaseHandler):
    """Route handler for adding tracks to a playlist."""

    @requires_login()
    @requires_params('songid')
    def post(self, playlistid):
        """POST /playlists/<playlistid>/add.

        Arguments:
            playlistid (str): Integer string identifying the playlist to add a track to.

        Parameters:
            songid (str): Integer string identifying the song to be added to the playlist.
        """
        user = users.util.get_user_from_request(self.request)
        if not music.util.owns_playlist(playlistid, user.guid):
            return self.HTTP_403(error='You don\'t own this playlist.')

        songid = self.request.data['songid']
        music.util.add_song_to_playlist(playlistid, songid)
        return self.HTTP_200()

class RemoveFromPlaylist(BaseHandler):
    """Route handler for removing tracks from a playlist."""

    @requires_login()
    @requires_params('songid')
    def post(self, playlistid):
        """POST /playlists/<playlistid>/remove.

        Arguments:
            playlistid (str): Integer string identifying the playlist to remove a track from.

        Parameters:
            songid (str): Integer string identifying the song to be removed from the playlist.
        """
        user = users.util.get_user_from_request(self.request)
        if not music.util.owns_playlist(playlistid, user.guid):
            return self.HTTP_403(error='You don\'t own this playlist.')

        songid = self.request.data['songid']
        music.util.remove_song_from_playlist(playlistid, songid)
        return self.HTTP_200()

class SetPlaylistPublicity(BaseHandler):
    """Route handler for updating the public status of a playlist."""

    @requires_login()
    @requires_params('is_public')
    def post(self, playlistid):
        """POST /playlists/<playlistid>/set_publicity.

        Arguments:
            playlistid (str): Integer string identifying the playlist to update the publicity of.

        Parameters:
            is_public (str): Boolean string indicating whether the playlist should be made public.
        """
        user = users.util.get_user_from_request(self.request)
        if not music.util.owns_playlist(playlistid, user.guid):
            return self.HTTP_403(error='You don\'t own this playlist.')

        publicity = self.request.data['is_public']

        # Convert input to boolean as appropriate
        if not isinstance(publicity, bool):
            if isinstance(publicity, str):
                publicity = publicity.lower()
                if publicity == 'true':
                    publicity = True
                elif publicity == 'false':
                    publicity = False
                else:
                    return self.HTTP_400(error='Invalid publicity string.')
            else:
                return self.HTTP_400(error='Invalid publicity type.')

        if music.util.set_playlist_publicity(playlistid, publicity):
            return self.HTTP_200()
        else:
            return self.HTTP_400(error='Unable to update publicity.')