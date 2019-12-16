#!/usr/bin/env python
# -*- coding: utf-8 -*-
# Filename: users/util.py

# Native python imports
import logging, threading, os, random, operator, datetime

# Local file imports
from music.models import Playlist, Song, RefreshState
from settings import MOUNTED_FOLDER, MISSING_ARTWORK_FILE, MUSIC_FOLDER
from users.models import User
from util.util import Session, access_db

# PIP library imports
import eyed3
import sqlalchemy
from sqlalchemy.orm.exc import NoResultFound, MultipleResultsFound
from sqlalchemy import or_, func

# Variables and config
logger = logging.getLogger(__name__)
logging.basicConfig(level=logging.INFO)

def fetch_track_info(songid):
    """Fetch detailed information about a given track.

    Arguments:
        songid (str): Integer string identifying the track to fetch information on.
    """
    with access_db() as db_conn:
        try:
            track = db_conn.query(Song).get(songid)
        except:
            logger.warn(f"Exception encountered while trying to access song id: {songid}")
            return None
        else:
            if not track:
                logger.warn(f"No song found with id {songid}.")
                return None
            return {
                'title': track.track_name,
                'artist': track.artist_name,
                'album': track.album_name,
                'track_length': track.track_length,
                'id': track.id,
            }

def fetch_track_path(songid):
    """Fetch the file path for a given track id.
    
    Arguments:
        songid (str): Integer string identifying the song to fetch the file path for.
    """
    with access_db() as db_conn:
        try:
            track = db_conn.query(Song).get(songid)
        except:
            logger.warn(f"Exception encountered while trying to access song id: {songid}")
            return None
        else:
            if not track:
                logger.warn(f"No song found with id {songid}.")
                return None
            return track.track_path

def fetch_artwork_path(songid):
    """Fetch the artwork file path for a given track id.
    
    Arguments:
        songid (str): Integer string identifying the song to fetch the artwork file path for.
    """
    track_path = fetch_track_path(songid)
    track_dir = os.path.dirname(track_path)

    # Iterate over all files in the same directory as the track.
    for f in os.listdir(track_dir):
        full_path = os.path.join(track_dir, f)
        # If the file ends with either .png or .jpg, we use that file.
        if os.path.isfile(full_path):
            if full_path.endswith('.png'):
                return full_path
            if full_path.endswith('.jpg'):
                return full_path
    logger.info(f'Missing artwork for song with id {songid}')
    return MISSING_ARTWORK_FILE

def get_all_tracks():
    """Fetch track info for all songs in the database."""
    with access_db() as db_conn:
        result = []
        all_tracks = db_conn.query(Song).all()

        # Sort by artist name, then album name, then track name.
        all_tracks.sort(key=lambda x: (x.artist_name and x.artist_name.lower() or '', 
                                       x.album_name and x.album_name.lower() or '', 
                                       x.track_name and x.track_name.lower() or ''))
        for track in all_tracks:
            track_info = {
                'title': track.track_name,
                'artist': track.artist_name,
                'album': track.album_name,
                'id': track.id,
                'length': track.track_length
            }
            result.append(track_info)
        return result
    return None

def add_track_to_database(track_info):
    """Add a track to the database.

    Arguments:
        track_info (dict): Specific track information to be entered into the database.
    """
    track_path = track_info['track_path']
    with access_db() as db_conn:
        # Make sure the track doesn't already exist
        exists = db_conn.query(Song)\
                        .filter(Song.track_path==track_path)\
                        .first()
        if exists:
            return False

        # Create and add ORM object to the database
        song = Song(track_name=track_info['title'],
                    artist_name=track_info['artist'],
                    album_name=track_info['album'],
                    track_path=track_info['track_path'],
                    track_length=track_info['track_length'])
        db_conn.add(song)
        db_conn.commit()
        return True
    return False

def refresh_database():
    """Update the song database.

    Uses a single database entry to decide whether or not it's allowed to update the database.
    This is only allowed once every 5 minutes, at max.
    """
    with access_db() as db_conn:
        try:
            num_entries = db_conn.query(func.count(RefreshState.id)).count()
        except Exception as e:
            logger.warning('Exception while fetching count.')
            logger.warn(e)
        else:
            if num_entries == 0: # if there aren't any entries, make one
                state = RefreshState(last_refresh=datetime.datetime.now())
                db_conn.add(state)
                db_conn.commit()
            if num_entries > 1: # if there's more than one entry, delete them all and start over
                db_conn.query(RefreshState).delete()
                refresh_database()
            else: # if there's one entry, fetch it
                entry = db_conn.query(RefreshState).first()
                if entry.last_refresh:
                    # If the database has been refreshed at least once, check that it's been 5 minutes.
                    delta = entry.last_refresh - datetime.datetime.now()
                    if delta > datetime.timedelta(minutes=5):
                        # If 5 minutes have passed, allow an update.
                        t = threading.Thread(target=refresh_database_thread)
                        t.start()
                        entry.last_refresh = datetime.datetime.now()
                        db_conn.commit()
                else: 
                    # If the database has never been refreshed, then go for it
                    t = threading.Thread(target=refresh_database_thread)
                    t.start()
                    entry.last_refresh = datetime.datetime.now()
                    db_conn.commit()

def refresh_database_thread():
    """Walk through all files in the music folder, adding them to the database as necessary."""
    logger.info('Started refreshing.')

    try:
        # This handles directory walking, it's kind of nasty to use this iterator
        for dirpath, dirname, filename in os.walk(MUSIC_FOLDER):
            for f in filename:
                # Do nothing with non-mp3 tracks
                if not f.endswith('.mp3'):
                    continue
                full_file_path = os.path.join(dirpath, f)
                track_info = load_track_data(full_file_path)
                if track_info:
                    add_track_to_database(track_info)
    except:
        logger.warn('Exception encountered while refreshing database.')
    finally:
        # Return to a non-refreshing state once finished.
        with access_db() as db_conn:
            try:
                state = db_conn.query(RefreshState).one()
                state.is_refreshing=False
                db_conn.commit()
            except MultipleResultsFound as e:
                state = db_conn.query(RefreshState).first().delete()
                db_conn.commit()
                logger.info('Refreshing finished!')
                return
        logger.info('Refreshing finished!')

def load_track_data(track_path):
    """Open a track file in order to extract track info.

    Arguments:
        track_path (str): File path for the track to fetch information about.
    """
    # This silences some noisy notifications about malformed/missing info.
    eyed3.log.setLevel('ERROR')
    result = {}

    # Attempt to load the audiofile
    audiofile = None
    try:
        audiofile = eyed3.load(track_path)
    except Exception as e:
        logger.warn(f'Exception encountered while loading track: {track_path}')
        logger.warn(e)
        return None

    # Loading was successful, but returned None instead of a useable object.
    if not audiofile:
        logger.warn(f'eyed3 returned NoneType while loading track: {track_path}')
        return None

    # Load track title. If it doesn't exist, we don't want to display the track.
    try:
        result['title'] = audiofile.tag.title
    except:
        logger.warn(f'Track had no title: {track_path}')
        return None

    # Load track artist. It might not exist, and that's fine.
    try:
        result['artist'] = audiofile.tag.artist
    except:
        logger.info(f'Track has no artist: {track_path}')
        result['artist'] = ''

    # Load track album. It might not exist, and that's fine.
    try:
        result['album'] = audiofile.tag.album
    except:
        logger.info(f'Track has no album: {track_path}')
        result['album'] = ''

    # Fetch track length. If it doesn't exist, we don't want to display the track.
    try:
        time_secs = audiofile.info.time_secs
    except:
        logger.warn(f'Track had no track length data: {track_path}')
        return None

    # Convert the audio length from seconds to a more readable number.
    minutes, seconds = divmod(int(time_secs), 60)
    hours, minutes = divmod(minutes, 60)
    if (hours > 0):
        track_length = "%02d:%02d:%02d" % (hours, minutes, seconds)
    else:
        track_length = "%02d:%02d" % (minutes, seconds)
    result['track_length'] = track_length
    result['track_path'] = track_path

    return result

def create_new_playlist(playlist_name, owner_guid, owner_name):
    """Create a new playlist for a user.

    Arguments:
        playlist_name (str): Name for the new playlist.
        owner_guid (uuid): UUID of the user that is creating the playlist.
    """
    with access_db() as db_conn:
        new_playlist = Playlist(name=playlist_name, owner_guid=owner_guid)
        db_conn.add(new_playlist)
        db_conn.commit()

def owns_playlist(playlistid, owner_guid):
    """Check if a given user owns a specific playlist.

    Arguments:
        playlistid (str): Integer string identifying the playlist.
        owner_guid (uuid): UUID identifying the user to check against.
    """
    # Ensure both playlist and owner_guid are not None
    if (not playlistid) or (not owner_guid):
        logger.warn(f"Trying to check ownership with invalid playlistid of owner_guid.")
        return False

    with access_db() as db_conn:
        try:
            playlist = db_conn.query(Playlist).get(playlistid)
        except:
            logger.warn(f"Exception encountered while trying to access playlist id: {playlistid}.")
            return False
        else:
            if not playlist:
                logger.warn(f"No playlist found with id {playlistid}.")
                return False
            if playlist.owner_guid == owner_guid:
                return True

    logger.warn(f"User with guid {owner_guid} attempted to modify playlist they do not own with id {playlistid}.")
    return False

def get_playlist_from_id(playlistid):
    """Fetch the ORM object for a given playlist id.

    Arguments:
        playlistid (str): Integer string identifying a unique playlist.
    """
    if not playlistid:
        logger.warn(f"Trying to access playlist without id.")
        return None
    with access_db() as db_conn:
        try:
            playlist = db_conn.query(Playlist).get(playlistid)
        except:
            logger.warn(f"Exception encountered while trying to access playlist with id {playlistid}")
            return None
        else:
            return playlist

def get_playlist_data_from_id(playlistid):
    """Fetch information about a given playlist, as well as its tracks, from a unique id.

    Arguments:
        playlistid (str): Integer string identifying a unique playlist.

    Returns:
        playlist_data (dict): Dictionary containing information about the playlist, as well as its contents.
    """
    if not playlistid:
        logger.warn(f"Trying to access playlist without id.")
        return None
    with access_db() as db_conn:
        try:
            playlist = db_conn.query(Playlist)\
                              .get(playlistid)
        except:
            logger.warn(f"Exception encountered while trying to access playlist with id {playlistid}")
            return None
        else:
            if not playlist:
                return None
            owner_name = db_conn.query(User.username)\
                .filter(User.guid==playlist.owner_guid)\
                .scalar()
            playlist_data = {
                'tracks': [],
                'owner_name': owner_name,
                'name': playlist.name,
                'public': playlist.public,
            }
            if playlist.songs:
                # Sorts by artist name, then album name, then track name.
                sorted_songs = sorted(playlist.songs, key=lambda x: ((x.artist_name and x.artist_name.lower() or ''), 
                                                                     (x.album_name and x.album_name.lower() or ''), 
                                                                     (x.track_name and x.track_name.lower() or '')))
                for track in sorted_songs:
                    track_info = {
                        'title': track.track_name,
                        'artist': track.artist_name,
                        'album': track.album_name,
                        'id': track.id,
                        'length': track.track_length
                    }
                    playlist_data['tracks'].append(track_info)
            return playlist_data

def add_song_to_playlist(playlistid, songid):
    """Adds a given song to a specified playlist.

    Arguments:
        playlistid (str): Integer string identifying a unique playlist.
        songid (str): Integer string identifying a unique song.
    """
    with access_db() as db_conn:
        try:
            song = db_conn.query(Song).get(songid)
            playlist = db_conn.query(Playlist).get(playlistid)
        except:
            logger.warn(f"Exception encountered while trying to access db to add song {songid} to playlst {playlistid}")
            return
        else:
            if not song:
                logger.warn(f"Song {songid} does not exist.")
                return
            if not playlist:
                logger.warn(f"Playlist {playlistid} does not exist.")
                return

            playlist.songs.append(song)
            db_conn.commit()

def remove_song_from_playlist(playlistid, songid):
    """Removes a given song to a specified playlist.

    Arguments:
        playlistid (str): Integer string identifying a unique playlist.
        songid (str): Integer string identifying a unique song.
    """
    with access_db() as db_conn:
        try:
            song = db_conn.query(Song).get(songid)
            playlist = db_conn.query(Playlist).get(playlistid)
        except:
            logger.warn(f"Exception encountered while trying to access db to remove song {songid} from playlist {playlistid}")
            return
        else:
            if not song:
                logger.warn(f"Song {songid} does not exist.")
                return
            if not playlist:
                logger.warn(f"Playlist {playlistid} does not exist.")
                return

            try:
                playlist.songs.remove(song)
            except ValueError:
                pass
            else:
                db_conn.commit()

def get_public_playlists():
    """Fetch publicly available playlists."""
    result = {'playlists': []}
    with access_db() as db_conn:
        # Filter all playlists by publicity.
        public = db_conn.query(Playlist)\
                       .filter(Playlist.public==True)
        for playlist in public:
            # Fetch the playlist owner in order to get their username
            owner_name = db_conn.query(User.username)\
                .filter(User.guid==playlist.owner_guid)\
                .scalar()
            data = {
                'id': playlist.id,
                'name': playlist.name,
                'owner_name': owner_name,
            }
            result['playlists'].append(data)
    return result

def get_playlists_for_user(user_guid):
    """Fetch public playlists, and playlists owned by a specific user.

    Arguments:
        user_guid (uuid): UUID identifying the specific user to fetch playlists for.
    """
    result = {'playlists': []}
    with access_db() as db_conn:
        accessible = db_conn.query(Playlist)\
                       .filter(
                            or_(Playlist.owner_guid==user_guid,
                                Playlist.public==True)
                        )
        for playlist in accessible:
            owner_name = db_conn.query(User.username)\
                .filter(User.guid==user_guid)\
                .scalar()
            data = {
                'id': playlist.id,
                'name': playlist.name,
                'owner_name': owner_name,
            }
            result['playlists'].append(data)
    return result

def get_playlists_owned_by_user(user_guid):
    """Fetch playlists owned by a specific user.

    Arguments:
        user_guid (uuid): UUID identifying the specific user to fetch playlists for.
    """
    result = {'playlists': []}
    with access_db() as db_conn:
        accessible = db_conn.query(Playlist)\
                       .filter(Playlist.owner_guid==user_guid)
        for playlist in accessible:
            data = {
                'id': playlist.id,
                'name': playlist.name,
                'owner_name': playlist.owner_name,
            }
            result['playlists'].append(data)
    return result

