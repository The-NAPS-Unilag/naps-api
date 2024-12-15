from decouple import config


class Development:
    SECRET_KEY = config('SECRET_KEY')
    SQLALCHEMY_DATABASE_URI = config('DATABASE_URI')
    SQLALCHEMY_TRACK_MODIFICATIONS = True


class Staging:
    SECRET_KEY = config('TEST_SECRET_KEY')
    SQLALCHEMY_DATABASE_URI = config('TEST_DATABASE_URI')
    SQLALCHEMY_TRACK_MODIFICATIONS = True


class Production:
    SECRET_KEY = config('PROD_SECRET_KEY')
    SQLALCHEMY_DATABASE_URI = config('PROD_DATABASE_URI')
