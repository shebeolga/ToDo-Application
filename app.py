from flask import Flask, render_template, request, session, redirect, url_for, flash
from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
from werkzeug.security import generate_password_hash, check_password_hash
# from validate_email import validate_email
import logging
import os
from datetime import datetime
from database import *

logger = logging.getLogger(__name__)
logger.setLevel(logging.DEBUG)
formatter = logging.Formatter(
    "%(asctime)s - %(levelname)s - %(name)s - %(message)s",
    datefmt="%m/%d/%Y %I:%M:%S %p",
)

file_handler = logging.FileHandler("logfile.log", "w")
file_handler.setFormatter(formatter)

logger.addHandler(file_handler)

app = Flask(__name__)

# db_uri = "sqlite:///database.db"
app.config["DEBUG"] = True
app.config["SECRET_KEY"] = os.urandom(24)
# app.config["SQLALCHEMY_DATABASE_URI"] = db_uri
app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False

engine = create_engine("sqlite:///database.db")
Session = sessionmaker(engine)
db_session = Session()


@app.teardown_appcontext
def close_db(error):
    db_session.close()
    engine.dispose()


def get_current_user():
    result = None

    if "user" in session:
        user = session["user"]
        result = db_session.query(User).filter_by(user_id=user).first()

    return result


@app.route("/")
def index():
    user = get_current_user()

    return render_template("index.html", user=user)


@app.route("/signup", methods=["GET", "POST"])
def signup():
    user = get_current_user()

    if user:
        return redirect(url_for('my_tasks'))

    if request.method == "POST":
        name = request.form["name"]
        email = request.form["email"]

        # if not validate_email(email):
        #     error = "Your email is not valid"
        #     return render_template('sign_up.html', error=error)

        hashed_password = generate_password_hash(
            request.form["password"], method="sha256"
        )

        if not check_password_hash(hashed_password, request.form["repeat-password"]):
            error = "Password must be the same!"
            return render_template('sign_up.html', error=error)

        existing_user = db_session.query(User).filter_by(email=email).first()

        if existing_user:
            error = "User with this email already existis!"
            return render_template('sign_up.html', error=error)

        new_user = User(user_name=name, email=email, password=hashed_password)
        db_session.add(new_user)
        db_session.commit()

        session["user"] = str(new_user.user_id)

        return redirect(url_for("my_tasks"))

    return render_template("sign_up.html", user=user)


@app.route("/signin", methods=["GET", "POST"])
def signin():
    user = get_current_user()
    error = None

    if user:
        return redirect(url_for('my_tasks'))

    if request.method == "POST":
        email = request.form["email"]
        password = request.form["password"]

        user_result = db_session.query(User).filter_by(email=email).first()

        if user_result:
            if check_password_hash(user_result.password, password):
                session["user"] = str(user_result.user_id)
                return redirect(url_for("my_tasks"))
            else:
                error = "The password is incorrect!"
        else:
            error = "There is no such user. You have to register!"

    return render_template("sign_in.html", user=user, error=error)


@app.route("/signout")
def signout():
    session.clear()
    return redirect(url_for("index"))


@app.route("/my_tasks", methods=["GET", "POST"])
def my_tasks():
    user = get_current_user()

    if not user:
        return redirect(url_for('signin'))

    tasks = db_session.query(Task).filter_by(
        user_id=user.user_id).filter_by(done=0, deleted=0).all()

    return render_template("my_tasks.html", user=user, tasks=tasks)


@app.route("/new_task", methods=["GET", "POST"])
def new_task():
    user = get_current_user()

    if not user:
        return redirect(url_for('signin'))

    if request.method == "POST":
        task = request.form["task"]
        comment = request.form["comment"]
        try:
            request.form["urgent"]
            urgent = 1
        except:
            urgent = 0
        try:
            request.form["important"]
            important = 1
        except:
            important = 0

        new_task = Task(task_name=task, urgent=urgent, important=important)
        user.tasks.append(new_task)
        db_session.commit()

        if comment.strip():
            new_comment = Comment(comment=comment)
            new_task.comments.append(new_comment)
            db_session.commit()

        return redirect(url_for('my_tasks'))

    return render_template("new_task.html", user=user)


@app.route("/update/<task_id>", methods=['GET', 'POST'])
def update(task_id):
    user = get_current_user()

    if not user:
        return redirect(url_for('signin'))

    task = db_session.query(Task).filter_by(task_id=task_id).first()
    comments = db_session.query(Comment).filter_by(task_id=task_id).all()

    if request.method == "POST":
        new_task = request.form["task"]
        new_comment = request.form["comment"]
        try:
            request.form["urgent"]
            urgent = 1
        except:
            urgent = 0
        try:
            request.form["important"]
            important = 1
        except:
            important = 0

        task.task_name = new_task
        task.urgent = urgent
        task.important = important
        db_session.commit()

        if new_comment.strip():
            add_comment = Comment(comment=new_comment)
            task.comments.append(add_comment)
            db_session.commit()

        return redirect(url_for("my_tasks"))

    return render_template("update.html", user=user, task=task, comments=comments)


@app.route("/proceed_done/<task_id>")
def proceed_done(task_id):
    user = get_current_user()

    if not user:
        return redirect(url_for('signin'))

    task = db_session.query(Task).filter_by(task_id=task_id).first()

    task.done = True
    task.done_date = datetime.now()
    db_session.commit()

    return redirect(url_for('my_tasks'))


@app.route("/proceed_delete/<task_id>")
def proceed_delete(task_id):
    user = get_current_user()

    if not user:
        return redirect(url_for('signin'))

    task = db_session.query(Task).filter_by(task_id=task_id).first()

    task.deleted = True
    db_session.commit()

    return redirect(url_for('my_tasks'))


@app.route("/archive")
def archive():
    return "<h1>The page is under construction...</h1>"


@app.route("/reports")
def reports():
    return "<h1>The page is under construction...</h1>"


if __name__ == "__main__":
    app.run()
