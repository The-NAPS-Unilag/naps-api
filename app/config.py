from decouple import config


class Development:
    SECRET_KEY = config('SECRET_KEY')
    SQLALCHEMY_DATABASE_URI = config('DATABASE_URI')
    SQLALCHEMY_TRACK_MODIFICATIONS = True
    JWT_SECRET_KEY = config('JWT_SECRET_KEY')
    # Mail Settings
    MAIL_SERVER = "smtp.gmail.com"
    MAIL_PORT = 465
    MAIL_USE_TLS = False
    MAIL_USE_SSL = True
    MAIL_DEBUG = False
    MAIL_USERNAME = config("EMAIL_USER")
    MAIL_PASSWORD = config("EMAIL_PASSWORD")

class Staging:
    SECRET_KEY = config('TEST_SECRET_KEY')
    SQLALCHEMY_DATABASE_URI = config('TEST_DATABASE_URI')
    SQLALCHEMY_TRACK_MODIFICATIONS = True
    JWT_SECRET_KEY = config('JWT_SECRET_KEY')
    MAIL_SERVER = "smtp.gmail.com"
    MAIL_PORT = 465
    MAIL_USE_TLS = False
    MAIL_USE_SSL = True
    MAIL_DEBUG = False
    MAIL_USERNAME = config("EMAIL_USER")
    MAIL_PASSWORD = config("EMAIL_PASSWORD")


class Production:
    SECRET_KEY = config('PROD_SECRET_KEY')
    SQLALCHEMY_DATABASE_URI = config('PROD_DATABASE_URI')
    JWT_SECRET_KEY = config('JWT_SECRET_KEY')
    MAIL_SERVER = "smtp.gmail.com"
    MAIL_PORT = 465
    MAIL_USE_TLS = False
    MAIL_USE_SSL = True
    MAIL_DEBUG = False
    MAIL_USERNAME = config("EMAIL_USER")
    MAIL_PASSWORD = config("EMAIL_PASSWORD")