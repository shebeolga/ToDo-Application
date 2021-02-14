from flask import Flask, render_template, request, session, redirect, url_for, flash
from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
from werkzeug.security import generate_password_hash, check_password_hash
from validate_email import validate_email
import logging
import os
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
        result = db_session.query(User).filter_by(user_id=user)

    return result


@app.route("/")
def index():
    user = get_current_user()

    return render_template("index.html", user=user)


@app.route("/signup", methods=["GET", "POST"])
def signup():
    user = get_current_user()

    if request.method == "POST":
        name = request.form["name"]
        email = request.form["email"]

        if not validate_email(email):
            error = "Your email is not valid"
            return render_template('sign_up.html', error=error)

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

        return render_template("index.html", user=user)

    return render_template("sign_up.html", user=user)


@app.route("/signin", methods=["GET", "POST"])
def signin():
    user = get_current_user()

    if request.method == "POST":
        email = request.form["email"]
        password = request.form["password"]

        user_result = db_session.query(User).filter_by(email=email).first()

        if user_result:
            if check_password_hash(user_result.password, password):
                session["user"] = str(user_result.user_id)
                return render_template("index.html", user=user)
            else:
                error = "The password is incorrect!"
                return render_template('sign_in.html', error=error)
        else:
            error = "There is no such user. You have to register!"
            return render_template('sign_in.html', error=error)

    return render_template("sign_in.html", user=user)


@app.route("/signout")
def signout():
    # session.pop("user", None)
    session.clear()
    return redirect(url_for("index"))


@app.route("/new_task")
def new_task():
    return render_template("new_task.html")

if __name__ == "__main__":
    app.run()