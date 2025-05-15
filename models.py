from sqlalchemy import Column, ForeignKey, Integer, String, JSON, UniqueConstraint
from sqlalchemy.orm import relationship
from sqlalchemy.ext.mutable import MutableList
from database import Base


class SharePhoto(Base):
    __tablename__ = 'share_photos'

    photo_id = Column(Integer, ForeignKey('photos.photo_id', ondelete='CASCADE'), primary_key=True, nullable=False)
    user_id = Column(Integer, ForeignKey('users.user_id', ondelete='CASCADE'), primary_key=True, nullable=False)


class Follower(Base):
    __tablename__ = 'followers'

    user_id = Column(Integer, ForeignKey('users.user_id', ondelete='CASCADE'), primary_key=True)
    follower_id = Column(Integer, ForeignKey('users.user_id', ondelete='CASCADE'), primary_key=True)


class Rating(Base):
    __tablename__ = 'ratings'

    id = Column(Integer, primary_key=True, autoincrement=True)
    user_id = Column(Integer, ForeignKey('users.user_id', ondelete='CASCADE'), nullable=False)
    photo_id = Column(Integer, ForeignKey('photos.photo_id', ondelete='CASCADE'), nullable=True)
    photographer_id = Column(Integer, ForeignKey('users.user_id', ondelete='CASCADE'), nullable=True)
    photo_rating = Column(Integer, default=0)
    photographer_rating = Column(Integer, default=0)

    __table_args__ = (
        UniqueConstraint('user_id', 'photo_id', name='unique_photo_rating'),
        UniqueConstraint('user_id', 'photographer_id', name='unique_photographer_rating'),
    )


class Like(Base):
    __tablename__ = 'likes'

    user_id = Column(Integer, ForeignKey('users.user_id', ondelete='CASCADE'), primary_key=True)
    photo_id = Column(Integer, ForeignKey('photos.photo_id', ondelete='CASCADE'), primary_key=True)


class User(Base):
    __tablename__ = 'users'

    user_id = Column(Integer, primary_key=True, index=True)
    username = Column(String, index=True, nullable=False, unique=True)
    password = Column(String, nullable=False)
    role = Column(String, nullable=False, default='User')  
    rating = Column(Integer, default=0)


    photos = relationship("Photo", back_populates="owner", cascade="all, delete-orphan")
    followers = relationship("Follower", foreign_keys=[Follower.user_id], cascade="all, delete")
    following = relationship("Follower", foreign_keys=[Follower.follower_id], cascade="all, delete")
    ratings = relationship("Rating", foreign_keys=[Rating.user_id], cascade="all, delete")
    received_ratings = relationship("Rating", foreign_keys=[Rating.photographer_id], cascade="all, delete")
    likes = relationship("Like", cascade="all, delete")
    shared_photos = relationship("SharePhoto", foreign_keys=[SharePhoto.user_id], cascade="all, delete")


class Photo(Base):
    __tablename__ = 'photos'

    photo_id = Column(Integer, primary_key=True, index=True)
    owner_id = Column(Integer, ForeignKey('users.user_id', ondelete='CASCADE'), nullable=False)
    average_rating = Column(Integer, default=0)
    comments = Column(MutableList.as_mutable(JSON), default=lambda: [])
    tags = Column(String, default="")
    description = Column(String, default="")
    file_path = Column(String, nullable=False)


    owner = relationship("User", back_populates="photos")
    likes = relationship("Like", cascade="all, delete")
    ratings = relationship("Rating", foreign_keys=[Rating.photo_id], cascade="all, delete")
    shared_with = relationship("SharePhoto", foreign_keys=[SharePhoto.photo_id], cascade="all, delete")
