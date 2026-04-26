# Chatbot (Python)

## Setup
```bash
python3 -m venv .venv
source .venv/bin/activate
pip install torch nltk numpy

# NLTK data (once)
python3 -c "import nltk; nltk.download('punkt'); nltk.download('wordnet'); nltk.download('omw-1.4')"
```

## Run the GUI
```bash
python3 app.py
```

## Run the CLI
```bash
python3 chat.py
```
