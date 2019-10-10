from pycnic.core import WSGI, Handler

from music.routes import Songs, BuildDatabase, Audio, Artwork, RandomSong, Playlists
from music.routes import CreatePlaylist, AddToPlaylist, RemoveFromPlaylist, OwnedPlaylists
from users.routes import UsersRoutes, Register, Login, Logout, CurrentUser, SetUserVolume
from util.util import BaseHandler, engine
from util.routes import Remount, Restart

import music.models
import users.models
#from music.models import *
#from users.models import *
from util.models import Base

# This should initialize the database as necessary.
Base.metadata.create_all(engine)

class AcommpliceMusic(BaseHandler):
    def get(self):
        return self.success()

class Ping(BaseHandler):
    def get(self):
        return self.success({'msg': 'Pong!'})

class app(WSGI):
    """Acommplice API router main app.

    Launch on windows with:
        waitress-serve --listen=*:80 main:app
    Launch on unix with:
        gunicorn main:app
    """
    routes = [
        # 'Home' page -- empty data return
        ('/', AcommpliceMusic()),

        # 'Ping' page -- data return with a 'msg' that says 'Pong!'
        ('/ping', Ping()),

        ('/users/([\w\d\-_]*)', UsersRoutes()),
        ('/register', Register()),
        ('/login', Login()),
        ('/logout', Logout()),
        ('/current_user', CurrentUser()),
        ('/set_volume', SetUserVolume()),

        ('/songs', Songs()),
        ('/songs/(\d+)', Songs()),
        ('/songs/(\d+)/audio', Audio()),
        ('/songs/(\d+)/artwork', Artwork()),
        ('/songs/random', RandomSong()),

        ('/playlists', Playlists()),
        ('/playlists/(\d+)', Playlists()),
        ('/playlists/create', CreatePlaylist()),
        ('/playlists/owned', OwnedPlaylists()),
        ('/playlists/(\d+)/add', AddToPlaylist()),
        ('/playlists/(\d+)/remove', RemoveFromPlaylist()),

        ('/refresh', BuildDatabase()),
        ('/remount', Remount()),
        ('/restart', Restart()),
        #('/login', Login()),
        #('/logout', Logout()),
        #('/register', Register()),
        #('/register/([0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12})', Register()),
    ]

application = app