from sqlalchemy import (
    create_engine,
    Table,
    Column,
    Integer,
    String,
    Text,
    DateTime,
    Boolean,
    ForeignKey,
)
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship, sessionmaker
from datetime import datetime


engine = create_engine("sqlite:///database.db")
Base = declarative_base()


task_letter = Table(
    "task_letter",
    Base.metadata,
    Column("task_id", Integer, ForeignKey("tasks.task_id")),
    Column("letter_id", Integer, ForeignKey("letters.letter_id")),
)


class User(Base):
    __tablename__ = "users"
    user_id = Column(Integer, primary_key=True, autoincrement=True)
    user_name = Column(String, nullable=False)
    email = Column(String, nullable=False)
    password = Column(String, nullable=False)
    signup_date = Column(DateTime, default=datetime.now, nullable=False)
    tasks = relationship("Task")
    letters = relationship("Letter")


class Task(Base):
    __tablename__ = "tasks"
    task_id = Column(Integer, primary_key=True, autoincrement=True)
    user_id = Column(Integer, ForeignKey("users.user_id"))
    task_name = Column(String, nullable=False)
    urgent = Column(Boolean)
    important = Column(Boolean)
    create_date = Column(DateTime, default=datetime.now, nullable=False)
    done_date = Column(DateTime)
    done = Column(Boolean, default=0)
    deleted = Column(Boolean, default=0)
    comments = relationship("Comment")
    letters = relationship("Letter", secondary=task_letter)


class Comment(Base):
    __tablename__ = "comments"
    comment_id = Column(Integer, primary_key=True, autoincrement=True)
    task_id = Column(Integer, ForeignKey("tasks.task_id"))
    comment = Column(Text, nullable=False)
    add_date = Column(DateTime, default=datetime.now, nullable=False)


class Letter(Base):
    __tablename__ = "letters"
    letter_id = Column(Integer, primary_key=True, autoincrement=True)
    user_id = Column(Integer, ForeignKey("users.user_id"))
    sent_date = Column(DateTime, default=datetime.now, nullable=False)
    tasks = relationship("Task", secondary=task_letter)


if __name__ == "__main__":
    Base.metadata.create_all(engine)

    Session = sessionmaker(engine)
    session = Session()

    user = User(user_name="Olga", email="shebeolga@gmail.com",
                password="123456")
    session.add(user)

    # task = Task(user_id=1, task_name='New task', urgent=True, important=False, done=0, deleted=0)
    # session.add(task)

    # user = User(user_name='Max', email='max@gmail.com', password='1qazxsw2')
    # session.add(user)

    # task = Task(user_id=2, task_name='My task', urgent=False, important=True, done=0, deleted=0)
    # session.add(task)

    session.commit()

    # result = session.query(Users, Tasks).filter(Users.user_id == Tasks.user_id).all()

    # for user, task in result:
    #     print('Name:', user.user_name, 'Task:', task.task_name)

    # for u, t in session.query(Users, Tasks).filter(Users.user_id == Tasks.user_id).filter(Users.user_name == 'Olga').all():
    #     print("ID: {} Name: {} Task: {} Data: {}".format(u.user_id, u.user_name, t.task_name, t.task_create_date))
