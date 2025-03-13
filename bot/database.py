from sqlalchemy import create_engine, Column, Integer, String, ForeignKey, Table
from sqlalchemy.orm import declarative_base, sessionmaker, relationship

DATABASE_PATH = 'sqlite:///Database.db'

engine = create_engine(DATABASE_PATH)
Session = sessionmaker(bind=engine)
session = Session()

Base = declarative_base()

# Table for connecting users and groups (many-to-many relationship)
user_group_association = Table(
    'user_group_association', Base.metadata,
    Column('user_id', Integer, ForeignKey('Users.id'), primary_key=True),
    Column('group_id', Integer, ForeignKey('Group.id'), primary_key=True)
)


class User(Base):
    __tablename__ = 'Users'

    id = Column(Integer, primary_key=True)  # Telegram user.id
    name = Column(String, nullable=False)  # Telegram username
    token = Column(String, nullable=True)  # Yandex Music token
    count_of_sharing = Column(Integer, default=0)

    groups = relationship("Group", secondary=user_group_association, back_populates="users")
    shared_music = relationship("Music", back_populates="shared_by")


class Group(Base):
    __tablename__ = 'Group'

    id = Column(Integer, primary_key=True)
    name = Column(String, nullable=False)

    users = relationship("User", secondary=user_group_association, back_populates="groups")
    music = relationship("Music", back_populates="group")


class Music(Base):
    __tablename__ = 'Music'

    id = Column(Integer, primary_key=True)
    yandex_id = Column(Integer, nullable=False)  # Yandex Music track id
    title = Column(String, nullable=False)  # Artist and title of music
    type = Column(String, nullable=False)  # Track or album
    count_of_likes = Column(Integer, default=0)

    user_id = Column(Integer, ForeignKey('Users.id'))
    shared_by = relationship("User", back_populates="shared_music")

    group_id = Column(Integer, ForeignKey('Group.id'))
    group = relationship("Group", back_populates="music")


class Database:
    def init(self):
        pass

    def create_tables(self) -> None:
        Base.metadata.create_all(engine)

    # User functions

    def insert_user(self, user_id: int, user_name: str):
        user = session.query(User).filter(User.id == user_id).first()
        if not user:
            session.add(User(id=user_id, name=user_name))
            session.commit()

    def update_user_token(self, user_id: int, new_token: str) -> bool:  # TODO add token validity check
        user = session.query(User).filter(User.id == user_id).first()
        user.token = new_token
        session.commit()
        return True

    def get_user_statistic(self, user_id: int) -> dict:
        user = session.query(User).filter(User.id == user_id).first()
        return {'token': user.token is not None, 'count_of_sharing': user.count_of_sharing}

    def get_user_groups(self, user_id: int):
        user = session.query(User).filter(User.id == user_id).first()
        return user.groups

    def check_username(self, username: str) -> bool:
        user = session.query(User).filter(User.name == username).first()
        if user:
            return True
        else:
            return False

    def get_token(self, user_id: int) -> str:
        user = session.query(User).filter(User.id == user_id).first()
        return user.token

    def incr_count_of_sharing(self, user_id: int) -> None:
        user = session.query(User).filter(User.id == user_id).first()
        user.count_of_sharing += 1

    def get_user_sharing(self, user_id: int):
        user = session.query(User).filter(User.id == user_id).first()
        return user.shared_music

    def get_username(self, user_id: int) -> str:
        user = session.query(User).filter(User.id == user_id).first()
        return str(user.name)

    # Group functions

    def create_group(self, name: str, user_id: int) -> bool:
        group = Group(name=name)
        user = session.query(User).filter(User.id == user_id).first()
        group.users = [user]
        session.add(group)
        session.commit()
        return True

    def get_group_name(self, group_id: int) -> str:
        group = session.query(Group).filter(Group.id == group_id).first()
        return str(group.name)

    def delete_group(self, group_id: int) -> bool:
        group = session.query(Group).filter(Group.id == group_id).first()
        if not group:
            return False

        session.delete(group)
        session.commit()
        return True

    def get_group_users(self, group_id: int):
        group = session.query(Group).filter(Group.id == group_id).first()
        return group.users

    def add_user_to_group(self, group_id: int, user_name: str) -> bool:
        group = session.query(Group).filter(Group.id == group_id).first()

        user = session.query(User).filter(User.name == user_name).first()
        if user:
            group.users.extend([user])
            session.commit()
            return True
        else:
            return False

    def get_group_sharing(self, group_id: int):
        group = session.query(Group).filter(Group.id == group_id).first()
        return group.music

    # Music functions

    def insert_music(self, track_id: int, title: str, type: str, user_id: Integer, group_id: Integer) -> None:
        session.add(Music(yandex_id=track_id, title=title, type=type, user_id=user_id, group_id=group_id))
        session.commit()
