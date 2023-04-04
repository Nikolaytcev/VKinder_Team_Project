import os
from typing import List

from dotenv import load_dotenv
import psycopg2
import sqlalchemy
from sqlalchemy import func
from sqlalchemy.orm import sessionmaker

from VKinder_db.models import create_tables, Users, Relations, Status


class DBHandler:
    def __init__(self, db_name: str):
        load_dotenv()
        self.DB = os.getenv('DB')
        self.DB_USER = os.getenv('DB_USER')
        self.DB_PASS = os.getenv('DB_PASS')
        self.DB_HOST = os.getenv('DB_HOST')
        self.DB_PORT = os.getenv('DB_PORT')
        self.db_name = db_name
        self.create_db()

    def get_DSN_from_dotenv(self) -> str:
        """Return DSN formed by data from .env file"""
        DSN = f"{self.DB}://{self.DB_USER}:{self.DB_PASS}@{self.DB_HOST}:{self.DB_PORT}/{self.db_name}"
        return DSN

    def create_db(self):
        """Create DB with db_name if not exists"""
        conn = psycopg2.connect(
            user=self.DB_USER,
            password=self.DB_PASS,
            host=self.DB_HOST,
            port=self.DB_PORT
        )
        conn.autocommit = True
        cursor = conn.cursor()
        cursor.execute(f"SELECT 1 FROM pg_catalog.pg_database WHERE datname = '{self.db_name}'")
        exists = cursor.fetchone()
        if not exists:
            cursor.execute(f'CREATE DATABASE {self.db_name}')
        conn.close()


class DBService:
    def __init__(self, session):
        self.session = session
        self.__fill_statuses()

    def __fill_statuses(self):
        filled = self.session.query(func.count(Status.status_id)).scalar()
        if not filled:
            status = Status(status_id=1, status='Favorite')
            self.session.add(status)
            status = Status(status_id=2, status='Blacklist')
            self.session.add(status)
            self.session.commit()

    def add_user(self, user_info: List):
        """
        Insert user into DB
        :param user_info: List of str [first name, last name, gender, city, profile link]
        """
        if len(user_info) == 4:
            user_info.append("Unknown")
        user = Users(user_id=user_info[0],
                     first_name=user_info[1],
                     last_name=user_info[2],
                     gender=user_info[3],
                     city=user_info[4])
        self.session.add(user)
        self.session.commit()

    def check_user_in_db(self, user_id):
        return self.session.query(Users.user_id).filter(Users.user_id == user_id)

    def add_relation(self, from_user_id: int, to_user_id: int, status='Favorite'):
        """
        Add relation from one user to another
        :param from_user_id: profile id of user who add relation
        :param to_user_id: profile id who will be added
        :param status: 'Favorite' or 'Blacklist'
        """
        if status not in ('Favorite', 'Blacklist'):
            print("Недопустимое значение статуса, укажите 'Favorite' или 'Blacklist'")
            return
        status = 1 if status == 'Favorite' else 2
        relation = Relations(from_user_id=from_user_id, to_user_id=to_user_id, status_id=status)
        self.session.add(relation)
        self.session.commit()

    def get_favorite_list(self, user_id):
        """
        Return list of favorites, which are tuples, each tuple contains user info
        :param user_id: vk profile id
        :return: favorites: list of tuples
        """
        favorites = self.session.query(Users.user_id,
                                       Users.first_name,
                                       Users.last_name,
                                       Users.gender,
                                       Users.city)\
            .join(Relations, Users.user_id == Relations.to_user_id) \
            .join(Status, Relations.status_id == Status.status_id) \
            .filter(Relations.from_user_id == user_id, Status.status == 'Favorite').all()
        return favorites

    def get_blocked_list(self, user_id):
        """
        Return list of blocked, which are tuples, each tuple contains user info
        :param user_id: vk profile id
        :return: blocked: list of tuples
        """
        blocked = self.session.query(Users.user_id,
                                     Users.first_name,
                                     Users.last_name,
                                     Users.gender,
                                     Users.city) \
            .join(Relations, Users.user_id == Relations.to_user_id) \
            .join(Status, Relations.status_id == Status.status_id) \
            .filter(Relations.from_user_id == user_id, Status.status == 'Blacklist').all()
        return blocked


def connect_to_db(db_name):
    """
    Provide creation of DB (if not exists) and connection to ORM model of DB
    :param db_name: name of db for work
    :return: service for work in outside files
    """
    db_handler = DBHandler(db_name)
    DSN = db_handler.get_DSN_from_dotenv()
    engine = sqlalchemy.create_engine(DSN)
    create_tables(engine)
    Session = sessionmaker(bind=engine)
    session = Session()
    with session:
        service = DBService(session)
        return service
