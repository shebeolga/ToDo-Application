import os


class Config():
    pass


class DevConfig(Config):
    # db_uri = "sqlite:///database.db"
    DEBUG = True
    SECRET_KEY = os.urandom(24)
    # app.config["SQLALCHEMY_DATABASE_URI"] = db_uri
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    MAIL_SERVER = "smtp.gmail.com"
    MAIL_PORT = 587
    MAIL_USERNAME = "shebeolga@gmail.com"
    MAIL_PASSWORD = "o1l1g1a1"
    MAIL_USE_TLS = True
    MAIL_USE_SSL = False
    MAIL_DEFAULT_SENDER = "support@myway.com"


class ProdConfig(Config):
    pass
