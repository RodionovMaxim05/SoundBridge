from sqlalchemy import (
    create_engine,
    Column,
    Integer,
    String,
    ForeignKey,
    Table,
    Float,
    UniqueConstraint,
)
from sqlalchemy.orm import declarative_base, sessionmaker, relationship

DATABASE_PATH = "sqlite:///Database.db"

engine = create_engine(DATABASE_PATH)
Session = sessionmaker(bind=engine)
session = Session()

Base = declarative_base()

# Table for connecting users and groups (many-to-many relationship)
user_group_association = Table(
    "user_group_association",
    Base.metadata,
    Column("user_id", Integer, ForeignKey("Users.id"), primary_key=True),
    Column("group_id", Integer, ForeignKey("Group.id"), primary_key=True),
)


class User(Base):
    """
    Represents a user.

    Relationships:
        ratings: List of ratings the user gave.
        groups: Groups the user belongs to.
        shared_music: Music shared by the user.
        group_playlists: Playlist info per group.
    """

    __tablename__ = "Users"

    id = Column(Integer, primary_key=True)  # Telegram user.id
    name = Column(String, nullable=False)  # Telegram username
    token = Column(String, nullable=True)  # Yandex Music token
    count_of_sharing = Column(Integer, default=0)
    count_of_ratings = Column(Integer, default=0)

    ratings = relationship("MusicRating", back_populates="user")
    groups = relationship(
        "Group", secondary=user_group_association, back_populates="users"
    )
    shared_music = relationship("Music", back_populates="shared_by")
    group_playlists = relationship("UserGroupPlaylist", back_populates="user")


class Group(Base):
    """
    Represents a group of users.

    Relationships:
        users: Members of the group.
        music: Shared music in the group.
        user_playlists: Playlist info per user in this group.
    """

    __tablename__ = "Group"

    id = Column(Integer, primary_key=True)
    name = Column(String, nullable=False)
    creator_id = Column(Integer, ForeignKey("Users.id"), nullable=False)

    users = relationship(
        "User", secondary=user_group_association, back_populates="groups"
    )
    music = relationship("Music", back_populates="group")
    user_playlists = relationship("UserGroupPlaylist", back_populates="group")


class UserGroupPlaylist(Base):
    """
    Stores Yandex Music playlist info for each user in a group.
    First of all, it is necessary to save playlist_kind for each user in each group.

    Relationships:
        user: Related User object.
        group: Related Group object.
    """

    __tablename__ = "UserGroupPlaylist"

    user_id = Column(Integer, ForeignKey("Users.id"), primary_key=True)
    group_id = Column(Integer, ForeignKey("Group.id"), primary_key=True)
    uid = Column(Integer, nullable=False)
    kind = Column(String, nullable=False)

    user = relationship("User", back_populates="group_playlists")
    group = relationship("Group", back_populates="user_playlists")


class Music(Base):
    """
    Represents a track or album shared by a user.

    Relationships:
        shared_by: User who shared the music.
        group: Group where it was shared.
        ratings: Ratings given to this music.
    """

    __tablename__ = "Music"

    id = Column(Integer, primary_key=True)
    yandex_id = Column(Integer, nullable=False)  # Yandex Music track id
    title = Column(String, nullable=False)  # Artist and title of music
    type_of_music = Column(String, nullable=False)  # Track or album
    message = Column(String, nullable=False)  # Text from user
    photo_uri = Column(String, nullable=False)
    average_mark = Column(Float, default=0)
    count_of_ratings = Column(Integer, default=0)

    ratings = relationship("MusicRating", back_populates="music")

    user_id = Column(Integer, ForeignKey("Users.id"))
    shared_by = relationship("User", back_populates="shared_music")

    group_id = Column(Integer, ForeignKey("Group.id"))
    group = relationship("Group", back_populates="music")


class MusicRating(Base):
    """
    Represents a rating given by a user to a specific piece of music.
    There is a unique constraint on (user_id, music_id) — one rating per user per music.

    Relationships:
        user: Who rated.
        music: What was rated.
    """

    __tablename__ = "MusicRating"

    id = Column(Integer, primary_key=True)
    user_id = Column(Integer, ForeignKey("Users.id"), nullable=False)
    music_id = Column(Integer, ForeignKey("Music.id"), nullable=False)
    rating = Column(Integer, nullable=False)

    user = relationship("User")
    music = relationship("Music")

    __table_args__ = (
        UniqueConstraint("user_id", "music_id", name="unique_user_music_rating"),
    )


class Database:
    """Main class for all database operations."""

    def create_tables(self) -> None:
        """Creates all tables in the DB if they don`t exist."""
        Base.metadata.create_all(engine)

    # User functions

    def insert_user(self, user_id: int, user_name: str):
        """Adds a new user if not exists."""
        user = session.query(User).filter(User.id == user_id).first()
        if not user:
            session.add(User(id=user_id, name=user_name))
            session.commit()

    def update_user_token(self, user_id: int, new_token: str):
        """Updates user's Yandex Music token."""
        user = session.query(User).filter(User.id == user_id).first()
        user.token = new_token
        session.commit()

    def get_user_statistic(self, user_id: int) -> dict:
        """
        Returns user statistics:
        whether there is a token, number of shared links, ratings, and average scores.
        """
        user = session.query(User).filter(User.id == user_id).first()
        return {
            "token": user.token is not None,
            "count_of_sharing": user.count_of_sharing,
            "count_of_ratings": user.count_of_ratings,
            "score_of_shared_music": self.get_average_score_of_shared_music(user_id),
            "score_of_rated_music": self.get_average_score_of_rated_music(user_id),
        }

    def get_user_groups(self, user_id: int):
        """Returns all groups user belongs to."""
        user = session.query(User).filter(User.id == user_id).first()
        return user.groups

    def check_username(self, username: str) -> bool:
        """Checks if username exists."""
        user = session.query(User).filter(User.name == username).first()
        return bool(user)

    def get_token(self, user_id: int) -> str:
        """Gets user`s Yandex Music token."""
        user = session.query(User).filter(User.id == user_id).first()
        return user.token

    def incr_count_of_sharing(self, user_id: int) -> None:
        """Increments number of shared items."""
        user = session.query(User).filter(User.id == user_id).first()
        user.count_of_sharing += 1

    def get_user_sharing(self, user_id: int):
        """Returns all music shared by user."""
        user = session.query(User).filter(User.id == user_id).first()
        return user.shared_music

    def get_username(self, user_id: int) -> str:
        """Returns username by ID."""
        user = session.query(User).filter(User.id == user_id).first()
        return str(user.name)

    def get_all_users(self):
        """Returns all users in DB."""
        return session.query(User).all()

    # Group functions

    def create_group(self, name: str, user_id: int):
        """Creates a new group and adds creator as member."""
        group = Group(name=name, creator_id=user_id)
        user = session.query(User).filter(User.id == user_id).first()
        group.users = [user]
        session.add(group)
        session.commit()

    def get_group_name(self, group_id: int) -> str | None:
        """Returns group name by ID."""
        group = session.query(Group).filter(Group.id == group_id).first()
        return str(group.name) if group else None

    def delete_group(self, user_id: int, group_id: int):
        """
        Deletes a group and all its related data if the user is the creator,
        or removes the user from the group if they are not the creator.
        """
        group = session.query(Group).filter(Group.id == group_id).first()

        if group.creator_id == user_id:
            session.query(UserGroupPlaylist).filter_by(group_id=group_id).delete()
            group.users.clear()
            session.delete(group)
        else:
            user = session.query(User).get(user_id)
            user.groups.remove(group)
            session.query(UserGroupPlaylist).filter_by(
                user_id=user_id, group_id=group_id
            ).delete()

        session.commit()

    def get_group_users(self, group_id: int):
        """Returns list of users in a group."""
        group = session.query(Group).filter(Group.id == group_id).first()
        return group.users

    def add_user_to_group(self, group_id: int, user_name: str):
        """Adds a user to the group by username."""
        group = session.query(Group).filter(Group.id == group_id).first()
        user = session.query(User).filter(User.name == user_name).first()
        group.users.extend([user])
        session.commit()

    def get_group_sharing(self, group_id: int):
        """Returns all music shared in the group."""
        group = session.query(Group).filter(Group.id == group_id).first()
        return group.music

    def delete_track(self, track_id: int):
        """Deletes a track."""
        track = session.query(Music).get(track_id)

        session.query(MusicRating).filter_by(music_id=track_id).delete()
        session.delete(track)
        session.commit()

    # UserGroupPlaylist functions

    def create_playlist_for_user_in_group(
        self, user_id: int, group_id: int, playlist_kind: str, uid: int
    ):
        """Saves Yandex Music playlist info for a user in a group."""
        session.add(
            UserGroupPlaylist(
                user_id=user_id, group_id=group_id, kind=playlist_kind, uid=uid
            )
        )
        session.commit()

    def get_playlist(self, user_id: int, group_id: int):
        """Gets playlist info for a user in a group."""
        return (
            session.query(UserGroupPlaylist)
            .filter(
                UserGroupPlaylist.user_id == user_id,
                UserGroupPlaylist.group_id == group_id,
            )
            .first()
        )

    def update_playlist_info(
        self, user_id: int, group_id: int, new_kind: int, new_uid: int
    ):
        """Updates the kind and uid of an existing user's playlist in a group."""

        playlist = (
            session.query(UserGroupPlaylist)
            .filter(
                UserGroupPlaylist.user_id == user_id,
                UserGroupPlaylist.group_id == group_id,
            )
            .first()
        )

        playlist.kind = new_kind
        playlist.uid = new_uid

        session.commit()

    # Music functions

    def insert_music(
        self,
        yandex_id: int,
        title: str,
        type_of_music: str,
        message: str,
        photo_uri: str,
        user_id: Integer,
        group_id: Integer,
    ):
        """Adds a new track/album to DB."""
        new_music = Music(
            yandex_id=yandex_id,
            title=title,
            type_of_music=type_of_music,
            message=message,
            photo_uri=photo_uri,
            user_id=user_id,
            group_id=group_id,
        )
        session.add(new_music)
        session.commit()

        return new_music.id

    def get_music_by_id(self, music_id: int):
        """Gets music by ID."""
        return session.query(Music).filter(Music.id == music_id).first()

    def update_average_rating(self, music_id: int):
        """Recalculates average rating for music."""
        ratings = session.query(MusicRating).filter_by(music_id=music_id).all()
        if ratings:
            avg = sum(r.rating for r in ratings) / len(ratings)
            music = session.query(Music).get(music_id)
            music.average_mark = avg
            music.count_of_ratings = len(ratings)

            session.commit()

    def rate_music(self, user_id: int, music_id: int, rating: int):
        """Adds or updates a rating for a track."""
        existing_rating = (
            session.query(MusicRating)
            .filter_by(user_id=user_id, music_id=music_id)
            .first()
        )

        if existing_rating:
            existing_rating.rating = rating
        else:
            new_rating = MusicRating(user_id=user_id, music_id=music_id, rating=rating)
            session.add(new_rating)

        self.update_average_rating(music_id)
        session.commit()

    def get_average_score_of_shared_music(self, user_id: int):
        """Calculates average score of music shared by the user."""
        user = session.query(User).filter(User.id == user_id).first()
        sum_of_marks = 0
        number_of_rated_tracks = 0

        for music in user.shared_music:
            sum_of_marks += music.average_mark
            number_of_rated_tracks += 1 if music.count_of_ratings > 0 else 0

        if number_of_rated_tracks > 0:
            return sum_of_marks / number_of_rated_tracks
        return "Пока никто не оценил"

    def get_average_score_of_rated_music(self, user_id: int):
        """Calculates average of ratings given by the user."""
        user = session.query(User).filter(User.id == user_id).first()

        if user.ratings:
            return sum(r.rating for r in user.ratings) / len(user.ratings)
        return "Пока вы не оценивали"
