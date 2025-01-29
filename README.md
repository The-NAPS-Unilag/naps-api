# naps-api

Microservices for the NAPS application.

### Installation

1. Clone the repository:
    ```sh
    git clone https://github.com/The-NAPS-Unilag/naps-api.git
    cd naps-api
    ```

2. Create and activate a virtual environment:
    ```sh
    python3 -m venv venv
    source venv/bin/activate
    ```

3. Install the dependencies:
    ```sh
    pip install -r requirements.txt
    ```

### Database Setup  (if you use the .env i gave, skip the db setup)

1. Initialize the database:
    ```sh
    flask db init
    ```

2. Apply migrations:
    ```sh
    flask db migrate -m "Initial migration"
    flask db upgrade
    ```

### Environment Variables

Create a `.env` file in the root directory and add the following environment variables:
```SECRET_KEY=
DATABASE_URI= you can use neon to get a servless postgres db

TEST_SECRET_KEY=
TEST_DATABASE_URI=

PROD_SECRET_KEY=
PROD_DATABASE_URI=

FLASK_ENV=
JWT_SECRET_KEY=

API_KEY=
EMAIL_USER=
EMAIL_PASSWORD=
```
### Running the Application

1. Start the Flask application:
    ```sh
    flask run (or python3 run.py)
    ```

2. The application will be available at `http://localhost:5000/`.

### Running Tests

1. To run the tests, use the following command:
    ```sh
    pytest
    ```

### Code Formatting

Before pushing changes, run the auto linter:
```sh
autopep8 --in-place --aggressive --aggressive $(git ls-files '*.py')
```

### ⚠️ after changes to DB schema run:
```
flask db migrate -m "update migration"
flask db upgrade
```

### Contributing
1. Fork the repository.
2. Create a new branch (git checkout -b feature-branch).
3. Commit your changes (git commit -m 'Add some feature').
4. Push to the branch (git push origin feature-branch).
5. Open a pull request.