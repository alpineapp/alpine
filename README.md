# Alpine Spaced Repetition Learing App

## Set up
For a new MacOS:
```
python3 -m venv alpine
source ./alpine/bin/activate
pip install --upgrade pip # to install pip version 20.2.4
pip install -r requirements.txt
```

## Test API
```
# Get authorization token
http POST http://localhost:5000/api/tokens --auth <username>:<password>
# Call using the http Python library
http GET http://localhost:5000/api/decks/1 "Authorization:Bearer <token>"
```
