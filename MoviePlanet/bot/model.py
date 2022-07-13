from sqlalchemy import Column, Integer, String, create_engine, Boolean, DateTime
from sqlalchemy.ext.declarative import declarative_base


Base = declarative_base()
engine = create_engine('sqlite:///base.db', echo=False)


class User(Base):
    __tablename__ = 'users'
    id = Column(Integer, primary_key=True)
    user_id = Column(String, unique=True, nullable=False)

    def __init__(self, user_id):
        self.user_id = user_id

    def __repr__(self):
        return f'User_id - {self.user_id}'


class Admin(Base):
    __tablename__ = 'admins'
    id = Column(Integer, primary_key=True)
    user_id = Column(String, unique=True, nullable=False)

    def __init__(self, user_id):
        self.user_id = user_id

    def __repr__(self):
        return f'User_id - {self.user_id}'


class Post(Base):
    __tablename__ = 'posts'
    id = Column(Integer, primary_key=True)
    post = Column(String())
    date_time = Column(DateTime())
    published = Column(Boolean())

    def __init__(self, post, date_time, published):
        self.post = post
        self.date_time = date_time
        self.published = published

    def __repr__(self):
        return f'id - {self.id} | date - {self.date_time} | published - {self.published}'


Base.metadata.create_all(engine)
