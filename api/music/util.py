import sqlalchemy
from sqlalchemy.orm.exc import NoResultFound, MultipleResultsFound
from sqlalchemy.orm import sessionmaker
from sqlalchemy import or_

import eyed3

import logging, threading, os, random

from settings import MOUNTED_FOLDER, MISSING_ARTWORK_FILE, MUSIC_FOLDER

from util.util import engine

from music.models import Playlist

Session = sessionmaker(bind=engine)

logger = logging.getLogger(__name__)
logging.basicConfig(level=logging.INFO)

class access_db:
    """Wrapper class to use when accessing the database.

    This automatically closes database connections on completion, 
    and is designed solely for convenience.

    Example:
    with access_db() as db_conn:
        do_stuff()
        db_conn.commit()
    """
    def __enter__(self):
        """Connects to the database and return the connection as part of the setup process."""
        self.db_conn = Session()
        return self.db_conn

    def __exit__(self, type, value, traceback):
        """Closes the database connection as part of the teardown process."""
        self.db_conn.close()

def fetch_track_info(songid):
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
    track_path = fetch_track_path(songid)
    track_dir = os.path.dirname(track_path)
    for f in os.listdir(track_dir):
        full_path = os.path.join(track_dir, f)
        if os.path.isfile(full_path):
            if full_path.endswith('.png'):
                return full_path
            if full_path.endswith('.jpg'):
                return full_path
    logger.info(f'Missing artwork for song with id {songid}')
    return MISSING_ARTWORK_FILE

def fetch_random_track_info():
    with access_db() as db_conn:
        try:
            track_num = random.randrange(0,db_conn.query(Song).count())
            track = db_conn.query(Song)[track_num]
        except:
            logger.warn(f"Exception encountered while trying to fetch random song.")
            return None
        else:
            if not track:
                logger.warn(f"No songs found while fetching random song.")
                return None
            return {
                'title': track.track_name,
                'artist': track.artist_name,
                'album': track.album_name,
                'track_length': track.track_length,
                'id': track.id,
            }

def get_all_tracks():
    with access_db() as db_conn:
        result = []
        all_tracks = db_conn.query(Song).all()
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
    track_path = track_info['track_path']
    with access_db() as db_conn:
        exists = db_conn.query(Song)\
                        .filter(Song.track_path==track_path)\
                        .first()
        if exists:
            logger.info(f'Track already exists in database: {track_path}')
            return False
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
    # Check if we're allowed to refresh the database right now.
    with access_db() as db_conn:
        try:
            state = db_conn.query(RefreshState).one()
            # We only ever want one thread to refresh
            #if state.is_refreshing:
                #logger.info('Currently refreshing, not launching thread.')
                #return
        except NoResultFound as e:
            # Create our only entry, and set its state.
            state = RefreshState(is_refreshing=True)
            db_conn.add(state)
            db_conn.commit()
            t = threading.Thread(target=refresh_database_thread)
            t.start()
        except MultipleResultsFound as e:
            # Remove the first non-refreshing state and return.
            first_state = db_conn.query(RefreshState)\
                                 .filter(RefreshState.is_refreshing==False)\
                                 .first().delete()
            db_conn.commit()
            return
        else:
            # Run this in a thread
            state.is_refreshing = True
            #refresh_database_thread()
            #state.is_refreshing = False
            #state.commit()
            db_conn.commit()
            t = threading.Thread(target=refresh_database_thread)
            t.start()

def refresh_database_thread():
    # Walk through all files and folders, and add them to the database as necessary
    logger.info('Started refreshing.')
    for dirpath, dirname, filename in os.walk(MUSIC_FOLDER):
        for f in filename:
            # Do nothing with non-mp3 tracks
            if not f.endswith('.mp3'):
                continue
            full_file_path = os.path.join(dirpath, f)
            track_info = load_track_data(full_file_path)
            if track_info:
                add_track_to_database(track_info)
    # We always want to return to non-refreshing state.
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
    eyed3.log.setLevel('ERROR')
    result = {}

    # Attempt to load the audiofile
    audiofile = None
    try:
        audiofile = eyed3.load(track_path)
    except Exception as e:
        print(e)
        logger.warn(f'Exception encountered while loading track: {track_path}')
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

    # Load track artist and album. These might not exist, and that's fine.
    try:
        result['artist'] = audiofile.tag.artist
    except:
        logger.info(f'Track has no artist: {track_path}')

    try:
        result['album'] = audiofile.tag.album
    except:
        logger.info(f'Track has no album: {track_path}')

    try:
        time_secs = audiofile.info.time_secs
    except:
        logger.warn(f'Track had no track length data: {track_path}')
        return None

    # Convert the audio from seconds to a more readable number.
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
    with access_db() as db_conn:
        new_playlist = Playlist(name=playlist_name, owner_guid=owner_guid, owner_name=owner_name)
        db_conn.add(new_playlist)
        db_conn.commit()

def owns_playlist(playlistid, owner_guid):
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

    logger.warn(f"Fallthrough occurred while fetching playlist with id {playlistid}")
    return None

def get_playlist_data_from_id(playlistid):
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
            playlist_data = {
                'tracks': [],
                'owner_name': playlist.owner_name,
                'name': playlist.name,
                'public': playlist.public,
            }
            if playlist.songs:
                for track in playlist.songs:
                    track_info = {
                        'title': track.track_name,
                        'artist': track.artist_name,
                        'album': track.album_name,
                        'id': track.id,
                        'length': track.track_length
                    }
                    playlist_data['tracks'].append(track_info)
            return playlist_data

    logger.warn(f"Fallthrough occurred while fetching playlist with id {playlistid}")
    return None

def add_song_to_playlist(playlistid, songid):
    with access_db() as db_conn:
        try:
            song = db_conn.query(Song).get(songid)
            playlist = db_conn.query(Playlist).get(playlistid)
        except:
            logger.warn(f"Exception encountered while trying to access db to add song {songid} to playlst {playlistid}")
            return
        else:
            if (not song):
                logger.warn(f"Song {songid} does not exist.")
                return
            if (not song) or (not playlist):
                logger.warn(f"Playlist {playlistid} does not exist.")
                return
            playlist.songs.append(song)
            db_conn.commit()

def remove_song_from_playlist(playlistid, songid):
    with access_db() as db_conn:
        try:
            song = db_conn.query(Song).get(songid)
            playlist = db_conn.query(Playlist).get(playlistid)
        except:
            logger.warn(f"Exception encountered while trying to access db to remove song {songid} from playlist {playlistid}")
            return
        else:
            if (not song):
                logger.warn(f"Song {songid} does not exist.")
                return
            if (not song) or (not playlist):
                logger.warn(f"Playlist {playlistid} does not exist.")
                return
            playlist.songs.remove(song)
            db_conn.commit()

def get_public_playlists():
    result = {'playlists': []}
    with access_db() as db_conn:
        public = db_conn.query(Playlist)\
                       .filter(Playlist.public==True)
        for playlist in public:
            data = {
                'id': playlist.id,
                'name': playlist.name,
                'owner_name': playlist.owner_name,
            }
            result['playlists'].append(data)
    return result

def get_playlists_for_user(user_guid):
    result = {'playlists': []}
    with access_db() as db_conn:
        accessible = db_conn.query(Playlist)\
                       .filter(
                            or_(Playlist.owner_guid==user_guid,
                                Playlist.public==True)
                        )
        for playlist in accessible:
            data = {
                'id': playlist.id,
                'name': playlist.name,
                'owner_name': playlist.owner_name,
            }
            result['playlists'].append(data)
    return result

from music.models import Song, RefreshState