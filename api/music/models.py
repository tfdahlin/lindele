import sqlalchemy
from sqlalchemy import create_engine, Table
from sqlalchemy import Column, Integer, String, ForeignKey, Boolean
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship

from util.models import GUID, HexByteString

from settings import db_uri, debug_sql_output

from settings import engine


Base = declarative_base()

association_table = Table('association', Base.metadata,
    Column('playlist_id', Integer, ForeignKey('playlist.id')),
    Column('song_id', Integer, ForeignKey('song.id'))
)

class Playlist(Base):
    __tablename__ = 'playlist'

    id = Column(Integer, primary_key=True)

    name = Column(String)

    public = Column(Boolean, default=False)

    owner_guid = Column(GUID)
    owner_name = Column(String)

    # relation to playlist
    songs = relationship(
        "Song",
        secondary=association_table,
        back_populates="playlists"
    )

class Song(Base):
    __tablename__ = 'song'

    id = Column(Integer, primary_key=True)

    track_name = Column(String)
    artist_name = Column(String, default='')
    album_name = Column(String, default='')

    track_path = Column(String)

    track_length = Column(String)

    # relationship to songs
    playlists = relationship(
        "Playlist",
        secondary=association_table,
        back_populates="songs"
    )

class RefreshState(Base):
    __tablename__ = 'refreshstate'

    id = Column(Integer, primary_key=True)

    is_refreshing = Column(Boolean)

Base.metadata.create_all(engine)