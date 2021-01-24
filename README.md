# Alpine Spaced Repetition Learing App

## Set up DEV environment
For a new MacOS:
```
python3 -m venv alpine
source ./alpine/bin/activate
pip install --upgrade pip # to install pip version 20.2.4
pip install -r requirements.txt
```

## Codebase format
Please use flake8 as your linter.
VS Code setting:
```
    "python.linting.flake8Args": [
        "--ignore=E402,E501,E128",
    ],
    "python.linting.ignorePatterns": [
        ".vscode/*.py",
        "**/site-packages/**/*.py",
        "**/lib/**/*.py"
    ],
```

## How to run unit tests
```
python tests.py
```

## Test API
```
# Get authorization token
http POST http://localhost:5000/api/tokens --auth <username>:<password>
# Call using the http Python library
http GET http://localhost:5000/api/decks/1 "Authorization:Bearer <token>"
```
