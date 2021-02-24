from flask import Flask, render_template, request, session, redirect, url_for, flash
from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
from sqlalchemy import func
from werkzeug.security import generate_password_hash, check_password_hash
# from validate_email import validate_email
import logging
import os
from datetime import datetime, timedelta
from database import *
# import mail
from flask_mail import Mail, Message

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

app.config["MAIL_SERVER"] = "smtp.gmail.com"
app.config["MAIL_PORT"] = 587
app.config["MAIL_USERNAME"] = "shebeolga@gmail.com"
app.config["MAIL_PASSWORD"] = "o1l1g1a1"
app.config["MAIL_USE_TLS"] = True
app.config["MAIL_USE_SSL"] = False
app.config["MAIL_DEFAULT_SENDER"] = "support@myway.com"

mail = Mail(app)

engine = create_engine("sqlite:///database.db")
Session = sessionmaker(engine)
db = Session()


@app.teardown_appcontext
def close_db(error):
    db.close()
    engine.dispose()


def get_current_user():
    result = None

    if "user" in session:
        user = session["user"]
        result = db.query(User).filter_by(user_id=user).first()

    return result


def count_types_of_tasks(query_tasks):
    types_of_tasks = {}
    types_of_tasks["all_tasks"] = query_tasks.count()

    urgent_important_tasks = query_tasks.filter_by(
        urgent=1, important=1).count()
    types_of_tasks["urgent_important_tasks"] = urgent_important_tasks
    urgent_not_important_tasks = query_tasks.filter_by(
        urgent=1, important=0).count()
    types_of_tasks["urgent_not_important_tasks"] = urgent_not_important_tasks
    not_urgent_important_tasks = query_tasks.filter_by(
        urgent=0, important=1).count()
    types_of_tasks["not_urgent_important_tasks"] = not_urgent_important_tasks
    not_urgent_not_important_tasks = query_tasks.filter_by(
        urgent=0, important=0).count()
    types_of_tasks["not_urgent_not_important_tasks"] = not_urgent_not_important_tasks

    return types_of_tasks


@app.route("/")
def index():
    user = get_current_user()

    return render_template("index.html", user=user)


@app.route("/register", methods=["GET", "POST"])
def register():
    user = get_current_user()

    if user:
        return redirect(url_for('my_tasks'))

    if request.method == "POST":
        name = request.form["name"]
        email = request.form["email"]

        # if not validate_email(email):
        #     error = "Your email is not valid"
        #     return render_template('register.html', error=error)

        hashed_password = generate_password_hash(
            request.form["password"], method="sha256"
        )

        if not check_password_hash(hashed_password, request.form["repeat-password"]):
            error = "Password must be the same!"
            return render_template('register.html', error=error)

        existing_user = db.query(User).filter_by(email=email).first()

        if existing_user:
            error = "User with this email already existis!"
            return render_template('register.html', error=error)

        new_user = User(user_name=name, email=email, password=hashed_password)
        db.add(new_user)
        db.commit()

        session["user"] = str(new_user.user_id)

        return redirect(url_for("my_tasks"))

    return render_template("register.html", user=user)


@app.route("/login", methods=["GET", "POST"])
def login():
    user = get_current_user()
    error = None

    if user:
        return redirect(url_for('my_tasks'))

    if request.method == "POST":
        email = request.form["email"]
        password = request.form["password"]

        user_result = db.query(User).filter_by(email=email).first()

        if user_result:
            if check_password_hash(user_result.password, password):
                session["user"] = str(user_result.user_id)
                # mail.send_register_letter(
                #     user_result.user_name, user_result.email)
                msg = Message("This is a letter", recipients=[
                    user_result.email])
                msg.body = f"{user_result.user_name}, you logged in the MyWay App"
                mail.send(msg)
                return redirect(url_for("my_tasks"))
            else:
                error = "The password is incorrect!"
        else:
            error = "There is no such user. You have to register!"

    return render_template("login.html", user=user, error=error)


@app.route("/logout")
def logout():
    session.clear()
    return redirect(url_for("index"))


@app.route("/my_tasks", methods=["GET", "POST"])
def my_tasks():
    user = get_current_user()

    if not user:
        return redirect(url_for('login'))

    tasks = db.query(Task).filter_by(
        user_id=user.user_id).filter_by(done=0, deleted=0).all()

    return render_template("my_tasks.html", user=user, tasks=tasks)


@app.route("/new_task", methods=["GET", "POST"])
def new_task():
    user = get_current_user()

    if not user:
        return redirect(url_for('login'))

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
        db.commit()

        if comment.strip():
            new_comment = Comment(comment=comment)
            new_task.comments.append(new_comment)
            db.commit()

        return redirect(url_for('my_tasks'))

    return render_template("new_task.html", user=user)


@app.route("/update/<task_id>", methods=['GET', 'POST'])
def update(task_id):
    user = get_current_user()

    if not user:
        return redirect(url_for('login'))

    task = db.query(Task).filter_by(task_id=task_id).first()
    comments = db.query(Comment).filter_by(task_id=task_id).all()

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
        db.commit()

        if new_comment.strip():
            add_comment = Comment(comment=new_comment)
            task.comments.append(add_comment)
            db.commit()

        return redirect(url_for("my_tasks"))

    return render_template("update.html", user=user, task=task, comments=comments)


@app.route("/proceed_done/<task_id>")
def proceed_done(task_id):
    user = get_current_user()

    if not user:
        return redirect(url_for('login'))

    task = db.query(Task).filter_by(task_id=task_id).first()

    if task.done:
        task.done = False
        task.done_date = None
    else:
        task.done = True
        task.done_date = datetime.now()
    db.commit()

    return redirect(url_for('my_tasks'))


@app.route("/proceed_delete/<task_id>")
def proceed_delete(task_id):
    user = get_current_user()

    if not user:
        return redirect(url_for('login'))

    task = db.query(Task).filter_by(task_id=task_id).first()

    task.deleted = True
    db.commit()

    return redirect(url_for('my_tasks'))


@app.route("/archive")
def archive():
    user = get_current_user()

    if not user:
        return redirect(url_for('login'))

    today = datetime.strftime(datetime.now(), '%Y-%m-%d')

    query_tasks = db.query(Task).\
        filter_by(user_id=user.user_id).\
        filter_by(done=1, deleted=0).\
        filter(func.DATE(Task.done_date) == today)

    tasks = query_tasks.all()

    count_tasks = count_types_of_tasks(query_tasks)

    return render_template("archive.html", user=user, tasks=tasks, counts=count_tasks)


# Impossible to combine this and previous function, because
# there'll be an error when we load the archive page for the first time.
@app.route("/show_archive/<period>")
def show_archive(period):
    user = get_current_user()

    if not user:
        return redirect(url_for('login'))

    today = datetime.strftime(datetime.now(), '%Y-%m-%d')
    end_point = datetime.now() - timedelta(days=int(period))
    end_point = datetime.strftime(end_point, '%Y-%m-%d')

    query_tasks = db.query(Task).\
        filter_by(user_id=user.user_id).\
        filter_by(done=1, deleted=0).\
        filter(func.DATE(Task.done_date) <= today,
               func.DATE(Task.done_date) >= end_point)

    tasks = query_tasks.all()

    count_tasks = count_types_of_tasks(query_tasks)

    return render_template("show_archive.html", user=user, tasks=tasks, counts=count_tasks)


@app.route("/show_period_archive/<start_date>&<end_date>")
def show_period_archive(start_date, end_date):
    user = get_current_user()

    if not user:
        return redirect(url_for('login'))

    query_tasks = db.query(Task).\
        filter_by(user_id=user.user_id).\
        filter_by(done=1, deleted=0).\
        filter(func.DATE(Task.done_date) >= start_date,
               func.DATE(Task.done_date) <= end_date)

    tasks = query_tasks.all()

    count_tasks = count_types_of_tasks(query_tasks)

    return render_template("show_period_archive.html", user=user, tasks=tasks, counts=count_tasks)


@app.route("/stats")
def stats():
    user = get_current_user()

    if not user:
        return redirect(url_for('login'))

    return render_template("stats.html", user=user)


if __name__ == "__main__":
    app.run()
