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
    shared_tracks = relationship("Track", back_populates="shared_by")


class Group(Base):
    __tablename__ = 'Group'

    id = Column(Integer, primary_key=True)
    name = Column(String, nullable=False)

    users = relationship("User", secondary=user_group_association, back_populates="groups")
    tracks = relationship("Track", back_populates="group")


class Track(Base):
    __tablename__ = 'Tracks'

    id = Column(Integer, primary_key=True)
    yandex_id = Column(Integer, nullable=False)  # Yandex Music track id
    title = Column(String, nullable=False)  # Artist and title of track
    count_of_likes = Column(Integer, default=0)

    user_id = Column(Integer, ForeignKey('Users.id'))
    shared_by = relationship("User", back_populates="shared_tracks")

    group_id = Column(Integer, ForeignKey('Group.id'))
    group = relationship("Group", back_populates="tracks")


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
        if user:
            user.token = new_token
            session.commit()
            print(f"Token updated for user id {user_id}.")
            return True
        else:
            print(f"User with id {user_id} not found.")
            return False

    def get_user_statistic(self, user_id: int) -> dict:
        user = session.query(User).filter(User.id == user_id).first()
        return {'token': user.token is not None, 'count_of_sharing': user.count_of_sharing}

    def get_all_users(self):
        return session.query(User).all()

    # Group functions

    def create_group(self, name: str, user: User) -> None:
        group = Group(name)
        group.users = [user]
        session.add(group)
        session.commit()

    def add_user_to_group(self, group_id: int, user_id: int):  # TODO not user_id, need username
        group = session.query(Group).filter(Group.id == group_id).first()
        if group:
            user = session.query(User).filter(User.id == user_id).first()
            if user:
                group.users.extend([user])
                session.commit()
                print(f"User {user_id} added to {group_id}.")
            else:
                print(f"User with id {user_id} not found.")
        else:
            print(f"Group with id {group_id} not found.")

    # Track functions

    def insert_track(self, track: Track, user_id: Integer, group_id: Integer) -> None:
        session.add(track)
        session.commit()
