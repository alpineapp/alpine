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
        "--ignore=E402,E501,E128,W503,W504",
    ],
    "python.linting.ignorePatterns": [
        ".vscode/*.py",
        "**/site-packages/**/*.py",
        "**/lib/**/*.py"
    ],
```

## Run unit tests
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

## Deploy to PROD
First, create a PR to `master` branch.

After merged, you can choose either way to deploy by pushing to GitHub:
1. Create a release, with its tag following this [guideline](https://alpineapp.atlassian.net/projects/DEV?selectedItem=com.atlassian.jira.jira-projects-plugin%3Arelease-page)
2. Create a tag with prefix "v", e.g.: `v-Abaddon-1.0`
