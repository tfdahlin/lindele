#!/usr/bin/env python
# -*- coding: utf-8 -*-
# Filename: main.py

# Native python imports

# Local file imports
import music.models, music.routes
import users.models, users.routes
import util.routes
from util.models import Base
from util.util import BaseHandler, engine

# PIP library imports
from pycnic.core import WSGI, Handler

class AcommpliceMusic(BaseHandler):
    """Base URL handler.

    This route behaves similarly to a ping route.
    """
    def get(self):
        """GET /"""
        return self.HTTP_200()

class Ping(BaseHandler):
    """Ping request handler.

    This should only really be used for testing connectivity.
    """
    def get(self):
        """GET /ping"""
        return self.HTTP_200({'msg': 'Pong!'})

class app(WSGI):
    """Music stream API router main app.

    Launch on windows with:
        waitress-serve --listen=*:80 main:app
    Launch on unix with:
        gunicorn -b 0.0.0.0:80 main:app
    """
    routes = [
        # 'Home' page -- empty data return
        ('/', AcommpliceMusic()),

        # 'Ping' page -- data return with a 'msg' that says 'Pong!'
        ('/ping', Ping()),

        # All things users.
        ('/users/([\w\d\-_]*)', users.routes.UsersRoutes()),
        ('/register', users.routes.Register()),
        ('/login', users.routes.Login()),
        ('/logout', users.routes.Logout()),
        ('/current_user', users.routes.CurrentUser()),
        ('/set_volume', users.routes.SetUserVolume()),

        # All things tracks
        ('/songs', music.routes.Songs()),
        ('/songs/(\d+)', music.routes.Songs()),
        ('/songs/(\d+)/audio', music.routes.Audio()),
        ('/songs/(\d+)/artwork', music.routes.Artwork()),

        # All things playlists
        ('/playlists', music.routes.Playlists()),
        ('/playlists/(\d+)', music.routes.Playlists()),
        ('/playlists/create', music.routes.CreatePlaylist()),
        ('/playlists/owned', music.routes.OwnedPlaylists()),
        ('/playlists/(\d+)/add', music.routes.AddToPlaylist()),
        ('/playlists/(\d+)/remove', music.routes.RemoveFromPlaylist()),

        # Server functionality
        ('/refresh', music.routes.BuildDatabase()),
        ('/remount', util.routes.Remount()),
        ('/restart', util.routes.Restart()),
    ]

application = app

# This should initialize the database as necessary.
Base.metadata.create_all(engine)