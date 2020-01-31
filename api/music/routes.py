#!/usr/bin/env python
# -*- coding: utf-8 -*-
# Filename: music/routes.py

# Native python imports
import logging, os, io
from wsgiref.util import FileWrapper

# Local code imports
import users.util, music.util
from util.decorators import requires_params, requires_login
from util.util import BaseHandler, mount_as_needed
from settings import MISSING_ARTWORK_FILE

# PIP library imports
from pycnic.core import Handler
from PIL import Image

# Variables and config
logger = logging.getLogger(__name__)
logging.basicConfig(level=logging.INFO)

class Songs(BaseHandler):
    """Route handler for fetching track information."""
    def get(self, songid=None):
        """GET /songs/[songid]

        Arguments:
            songid (str): Integer string identifying that info about a single song should be fetched.
        """
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
        else:
            tracks = music.util.get_all_tracks()
            data = {
                'tracks': tracks
            }

        return self.HTTP_200(data=data)

class Audio(BaseHandler):
    """Route handler for fetching track audio files."""
    def get(self, songid):
        """GET /songs/<songid>/audio

        Arguments:
            songid (str): Integer string identifying the track that should be served.
        """
        try:
            track_file = music.util.fetch_track_path(int(songid))
        except:
            logger.warn(f'Could not fetch track audio for song id: {songid}.')
            return self.HTTP_404(error='Invalid song id.')

        # Log which users listen to which songs.
        try:
            track_info = music.util.fetch_track_info(int(songid))
        except:
            logger.warn(f'Could not fetch track info for song id: {songid}.')
        else:
            user = None
            if users.util.is_logged_in(self.request):
                user = users.util.get_user_from_request(self.request)
                user = user.username
            else:
                user = 'Anonymous user'
            if track_info:
                logger.info(f'{user} is listening to {track_info["title"]} by {track_info["artist"]}')

        # Only mount if we actually need to load the file.
        # This is specifically for my setup where the media server may go to sleep
        #  and is separate from the main server, so it may need to be mounted before
        #  tracks can be opened.
        mount_as_needed()
        try:
            wrapper = FileWrapper(open(track_file, 'rb'))
        except OSError as e:
            logger.warn(f'Exception while loading track {songid}.')
            return self.HTTP_400(error='Could not load track.')
        else:
            self.response.set_header('Content-Type', 'audio/mpeg')
            self.response.set_header('Content-Length', str(os.path.getsize(track_file)))
            self.response.set_header('Accept-Ranges', 'bytes')
            return wrapper

class Artwork(BaseHandler):
    """Route handler for fetching track artwork files."""
    def get(self, songid):
        """GET /songs/<songid>/artwork

        Arguments:
            songid (str): Integer string identifying the track that should have its artwork served.
        """
        try:
            artwork_file = music.util.fetch_artwork_path(int(songid))
        except:
            logger.warn(f'Could not fetch track artwork for song id: {songid}.')
            return self.HTTP_404(error='Invalid song id.')

        try:
            wrapper, content_type, content_length = self.get_wrapper_and_header_info(artwork_file)
        except Exception as e:
            logger.warn(f'Could not access artwork file for track with id {songid}, or missing album artwork.')
            logger.critical(e)
            return self.HTTP_400(error='Error loading album artwork.')
        else:
            self.response.set_header('Content-Length', content_length)
            self.response.set_header('Accept-Ranges', 'bytes')
            self.response.set_header('Content-Type', content_type)
            return wrapper

    def get_wrapper_and_header_info(self, filename, error=False):
        wrapper = None
        try:
            wrapper = FileWrapper(open(filename, 'rb'))
        except OSError as e:
            logger.warn(f'Could not access artwork file: {filename}.')
            logger.info(f'Attempting to load {MISSING_ARTWORK_FILE} instead.')
            if error:
                raise e
            else:
                return get_file_wrapper_and_content_type(MISSING_ARTWORK_FILE, error=True)
        else:
            if filename.endswith('.png'):
                return wrapper, 'image/png', str(os.path.getsize(filename))
            elif filename.endswith('.jpg') or filename.endswith('.jpeg'):
                return wrapper, 'image/jpeg', str(os.path.getsize(filename))
            else:
                raise TypeError(f'File type could not be determined for {filename}')

class BuildDatabase(BaseHandler):
    """Route handler for building/refreshing the track database."""
    def get(self):
        """GET /refresh"""
        # Asynchronous thread that refreshes the database, so the user doesn't have to wait.
        music.util.refresh_database()
        # Return success immediately
        return self.HTTP_200()

class Playlists(BaseHandler):
    """Route handler for fetching playlist information."""
    def get(self, playlistid=None):
        """GET /playlists/[playlistid]

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
            # No need to return this information, so we strip it.
            del(playlist_data['public'])
            return self.HTTP_200(data=playlist_data)
        else:
            return self.HTTP_403(error='You cannot access this playlist.')

class OwnedPlaylists(BaseHandler):
    """Route handler for fetching owned playlists."""
    def get(self):
        """GET /playlists/owned"""
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
        """POST /playlists/create

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
        """POST /playlists/<playlistid>/add

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
        """POST /playlists/<playlistid>/remove

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