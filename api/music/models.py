#!/usr/bin/env python
# -*- coding: utf-8 -*-
# Filename: music/models.py
"""Model classes for music-related database objects."""

# Local file imports
from util.models import Base, GUID

# PIP library imports
import sqlalchemy
from sqlalchemy import Table
from sqlalchemy import Column, Integer, String, ForeignKey, Boolean, DateTime
from sqlalchemy.orm import relationship

# Variables and config
# Association table between tracks and playlists
association_table = Table('association', Base.metadata,
    Column('playlist_id', Integer, ForeignKey('playlist.id')),
    Column('song_id', Integer, ForeignKey('song.id'))
)

class Playlist(Base):
    """Playlist ORM.

    Attributes:
        __tablename__ (str): Name of database table
        id (int): Primary database key for lookup
        name (str): Name of the playlist
        public (bool): Determines whether the playlist is publicly shared or not.
        owner_guid (GUID): GUID identifying the user that created the playlist.
        owner_name (str): String identifying the user that created the playlist.
        songs (relationship): Many-to-many relationship with individual songs.
    """

    __tablename__ = 'playlist'

    id = Column(Integer, primary_key=True)

    name = Column(String)

    public = Column(Boolean, default=False)

    owner_guid = Column(GUID)
    owner_name = Column(String) # I think we can scrap this, and should instead fetch it.

    songs = relationship(
        "Song",
        secondary=association_table,
        back_populates="playlists"
    )

class Song(Base):
    """Playlist ORM.

    Attributes:
        __tablename__ (str): Name of database table
        id (int): Primary database key for lookup
        track_name (str): Title of a given track
        artist_name (str): Artist of a given track
        album_name (str): Album of a given track
        track_path (str): Location of a track's file
        track_length (str): Length of a given track
        playlists (relationship): Many-to-many relationship with individual playlists.
    """

    __tablename__ = 'song'

    id = Column(Integer, primary_key=True)

    track_name = Column(String)
    artist_name = Column(String, default='')
    album_name = Column(String, default='')

    track_path = Column(String)
    track_hash = Column(String)

    track_length = Column(String)

    file_missing = Column(Boolean, default=False)

    playlists = relationship(
        "Playlist",
        secondary=association_table,
        back_populates="songs"
    )

class RefreshState(Base):
    """RefreshState ORM.

    Attributes:
        __tablename__ (str): Name of database table
        id (int): Primary database key for lookup
        is_refreshing (bool): This is used for preventing multiple refreshes from occuring simultaneously,
            sort of like a mutex lock.
    """

    __tablename__ = 'refreshstate'

    id = Column(Integer, primary_key=True)

    last_refresh = Column(DateTime)