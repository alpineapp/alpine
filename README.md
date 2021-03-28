# Alpine Spaced Repetition Learing App

## Set up DEV environment
```
# For local development
brew install postgresql
python -m venv alpine
chmod -R +x alpine
pip install -r requirements.txt

# Build local environment with Docker
chmod -R +x scripts
./scripts/rebuild_docker.sh
```

### Python Docstring Generator
We use Google convention of Python Docstring.
If you use VSCode, install `Python Docstring Generator` extension.

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
    "python.linting.pylintArgs": [
        "--load-plugins",
        "pylint_flask_sqlalchemy",
        "pylint_flask",
    ],
```

## Run unit tests
### Install chromedriver for front-end tests
```
# MacOS
brew install chromedriver
# Manually verify
# Source: https://stackoverflow.com/questions/60362018 macos-catalinav-10-15-3-error-chromedriver-cannot-be-opened-because-the-de/64019725
cd $(which chromedriver)/..
xattr -d com.apple.quarantine chromedriver
```
### Run tests
```
python function_tests.py
```

## Test API
```
# Get authorization token
http POST http://localhost:5000/api/tokens --auth <username>:<password>
# Call using the http Python library
http GET http://localhost:5000/api/cards/1 "Authorization:Bearer <token>"
```

## Deploy to PROD
First, create a PR to `master` branch.

After merged, you can choose either way to deploy by pushing to GitHub:
1. Create a release, with its tag following this [guideline](https://alpineapp.atlassian.net/projects/DEV?selectedItem=com.atlassian.jira.jira-projects-plugin%3Arelease-page)
2. Create a tag with prefix "v", e.g.: `v-Abaddon-1.0`
