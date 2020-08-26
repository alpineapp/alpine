# Alpine Spaced Repetition Learing App

## Test API
```
# Get authorization token
http POST http://localhost:5000/api/tokens --auth <username>:<password>
# Call using the http Python library
http GET http://localhost:5000/api/decks/1 "Authorization:Bearer <token>"
```