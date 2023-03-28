import sqlalchemy as sq
from sqlalchemy.orm import declarative_base, relationship


Base = declarative_base()


class Users(Base):
    __tablename__ = "users"
    user_id = sq.Column(sq.Integer, primary_key=True)
    first_name = sq.Column(sq.String(length=50), nullable=False)
    last_name = sq.Column(sq.String(length=50), nullable=False)
    gender = sq.Column(sq.String(length=10))
    city = sq.Column(sq.String(length=100))
    profile_link = sq.Column(sq.String(length=300))


class Status(Base):
    __tablename__ = "status"
    status_id = sq.Column(sq.Integer, primary_key=True)
    status = sq.Column(sq.String(length=50))


class Relations(Base):
    __tablename__ = "relations"
    relation_id = sq.Column(sq.Integer, primary_key=True)
    from_user_id = sq.Column(sq.Integer, sq.ForeignKey("users.user_id"), nullable=False)
    to_user_id = sq.Column(sq.Integer, sq.ForeignKey("users.user_id"), nullable=False)
    status_id = sq.Column(sq.Integer, sq.ForeignKey("status.status_id"), nullable=False)

    from_user = relationship(Users, foreign_keys=from_user_id, backref='relation_from')
    to_user = relationship(Users, foreign_keys=to_user_id, backref='relation_to')
    status = relationship(Status, backref='relation_status')


def create_tables(engine):
    """Create all described tables"""
    Base.metadata.drop_all(engine)
    Base.metadata.create_all(engine)
