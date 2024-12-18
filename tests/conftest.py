import pytest
from app import create_app
from app.extensions import db


@pytest.fixture(scope="module")
def test_client():
    app = create_app('app.config.Staging')

    with app.test_client() as testing_client:
        with app.app_context():
            db.create_all()
        yield testing_client
        with app.app_context():
            db.drop_all()
