from pycnic.core import WSGI, Handler

#from users.routes import UsersRoutes, Login, Logout, Register
from music.routes import Songs, BuildDatabase, Audio
from util.util import success

class AcommpliceMusic(Handler):
    def get(self):
        return success()

class Ping(Handler):
    def get(self):
        return success({'msg': 'Pong!'})

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

        ('/songs', Songs()),
        ('/songs/(\d+)', Songs()),
        ('/songs/(\d+)/audio', Audio()),
        ('/refresh', BuildDatabase()),
        #('/login', Login()),
        #('/logout', Logout()),
        #('/register', Register()),
        #('/register/([0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12})', Register()),
    ]

application = app