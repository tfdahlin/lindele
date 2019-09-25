import sqlalchemy
from sqlalchemy import create_engine
from sqlalchemy import Column, Integer, String, ForeignKey, Boolean
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship

#from users.models import User

from settings import db_uri

from settings import debug_sql_output

engine = create_engine(db_uri, echo=debug_sql_output)
Base = declarative_base()

class Song(Base):
    __tablename__ = 'song'

    id = Column(Integer, primary_key=True)

    track_name = Column(String)
    artist_name = Column(String)
    album_name = Column(String)

    track_path = Column(String)

    track_length = Column(String)

    # Playlists is many-to-many

class Playlist(Base):
    __tablename__ = 'playlist'

    id = Column(Integer, primary_key=True)

    name = Column(String)
    # foreign key to user
    #owner = 
    public = Column(Boolean, default=False)

class RefreshState(Base):
    __tablename__ = 'refreshstate'

    id = Column(Integer, primary_key=True)

    is_refreshing = Column(Boolean)

Base.metadata.create_all(engine)