from pycnic.core import WSGI, Handler

from music.routes import Songs, BuildDatabase, Audio, Artwork, RandomSong, Playlists
from music.routes import CreatePlaylist, AddToPlaylist, RemoveFromPlaylist
from users.routes import UsersRoutes, Register, Login, Logout, CheckLoginStatus
from util.util import BaseHandler

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
        ('/login_status', CheckLoginStatus()),

        ('/songs', Songs()),
        ('/songs/(\d+)', Songs()),
        ('/songs/(\d+)/audio', Audio()),
        ('/songs/(\d+)/artwork', Artwork()),
        ('/songs/random', RandomSong()),

        ('/playlists', Playlists()),
        ('/playlists/(\d+)', Playlists()),
        ('/playlists/create', CreatePlaylist()),
        ('/playlists/(\d+)/add', AddToPlaylist()),
        ('/playlists/(\d+)/remove', RemoveFromPlaylist()),

        ('/refresh', BuildDatabase()),
        #('/login', Login()),
        #('/logout', Logout()),
        #('/register', Register()),
        #('/register/([0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12})', Register()),
    ]

application = app