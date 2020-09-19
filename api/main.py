#!/usr/bin/env python
# -*- coding: utf-8 -*-
# Filename: main.py
"""Main application.

When run on its own, configures the database for use.
Otherwise, provides WSGI functionality.
"""

# Native python imports
import sys, argparse

# Local file imports
import music.models, music.routes, music.util
import users.models, users.routes
import users.util
import util.routes
from util.models import Base
from util.util import BaseHandler, engine

# PIP library imports
from pycnic.core import WSGI, Handler

class Lindele(BaseHandler):
    """Base URL handler.

    This route behaves similarly to a ping route.
    """

    def get(self):
        """GET /."""
        return self.HTTP_200()

class Ping(BaseHandler):
    """Ping request handler.

    This should only really be used for testing connectivity.
    """

    def get(self):
        """GET /ping."""
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
        ('/', Lindele()),

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
        ('/playlists/(\d+)/set_publicity', music.routes.SetPlaylistPublicity()),

        # Server functionality
        ('/refresh', music.routes.BuildDatabase()),
        ('/remount', util.routes.Remount()),
        ('/restart', util.routes.Restart()),
    ]

def init_database():
    """Create database and relevant tables."""
    # This should initialize the database as necessary.
    print('Initializing database.')
    Base.metadata.create_all(engine)

def main():
    """Main function used for administrative tasks.

    Optional arguments:
        -a --make_admin [Email] (str): Email of a user to make an admin.
        -i --init_database: Flag to initialize database.
        -l --list_admins: Flag to list all admins in database.
    """
    parser = argparse.ArgumentParser(description="An open-source music streaming API.")
    parser.add_argument('-a', '--make_admin', metavar='Email', nargs=1, type=str, help='Email address of the user to make an admin')
    parser.add_argument('-l', '--list_admins', action="store_true", help='List accounts that are admins.')
    parser.add_argument('-i', '--init_database', action='store_true', help='Initialize the database.')
    args = parser.parse_args()

    if args.init_database:
        # Create the tables for the database
        init_database()
        # And asynchronously load the music
        music.util.refresh_database()
    elif args.list_admins:
        admins = users.util.get_all_admins()
        for admin_email, admin_username in admins:
            print(f'{admin_email} - {admin_username}')
    elif args.make_admin:
        print(f'Making user {args.make_admin} an admin.')
        success = users.util.make_user_admin(args.make_admin)
        if success:
            print(f'Successfully made {sys.argv[2]} an admin.')
        else:
            print(f'Failed to make {sys.argv[2]} an admin.')

application = app

if __name__ == '__main__':
    main()
