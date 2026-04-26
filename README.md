# E-commerce Chatbot

A Python chatbot for a CoffeeMugs e-commerce store. It can answer product questions, show available products, track orders, create orders, cancel orders, update delivery addresses, and let an admin update order status.

The project includes both a Tkinter GUI and a command-line chat interface.

## Features

- Intent classification with PyTorch
- Product catalog lookup from `products.csv`
- Order tracking and management through SQL Server
- CSV seeding from `orders.csv`
- GUI chat app with admin login support
- CLI chat app for terminal use
- Training script for rebuilding `data.pth` from `intents.json`

## Requirements

- Python 3.10 or newer
- SQL Server
- Microsoft ODBC Driver 18 for SQL Server
- Python packages from `requirements.txt`

## Setup

Create and activate a virtual environment:

```bash
python3 -m venv .venv
source .venv/bin/activate
```

Install dependencies:

```bash
pip install -r requirements.txt
```

Download NLTK data:

```bash
python3 -c "import nltk; nltk.download('punkt'); nltk.download('wordnet'); nltk.download('omw-1.4')"
```

## Database Configuration

The app uses SQL Server through `pyodbc`. Set `MSSQL_CONNECTION_STRING` before running the chatbot:

```bash
export MSSQL_CONNECTION_STRING="Server=127.0.0.1,1433;Database=ChatbotDb;User Id=sa;Password=your_password;TrustServerCertificate=yes;Encrypt=yes"
```

If this environment variable is not set, the app uses the fallback connection string in `db.py`.

On startup, the app creates the required `orders` and `users` tables if they do not already exist. It also seeds initial order data from `orders.csv` when the orders table is empty.

Default admin account:

```text
Username: admin
Password: admin123
```

## Train the Model

Run training when `data.pth` is missing or after editing `intents.json`:

```bash
python3 train.py
```

This creates or updates `data.pth`, which is required by the GUI and CLI chatbot.

## Run the GUI

```bash
python3 app.py
```

In the GUI, type `admin login` to sign in as an admin. Admin users can update order status.

## Run the CLI

```bash
python3 chat.py
```

Type `quit`, `exit`, or `bye` to leave the CLI chat.

## Test Responses

Run the response test script:

```bash
python3 generate_response.py
```

The script checks sample queries from `intents.json` and asks you to mark each generated response as correct or wrong.

## Important Files

- `app.py` - Tkinter GUI chatbot
- `chat.py` - command-line chatbot
- `train.py` - trains the intent classification model
- `generate_response.py` - manual response evaluation script
- `model.py` - PyTorch neural network
- `nltk_utils.py` - tokenization, lemmatization, and bag-of-words helpers
- `db.py` - SQL Server setup and order/user database functions
- `product_catalog.py` - product CSV loading and formatting
- `intents.json` - training phrases and chatbot responses
- `data.pth` - trained model data
- `orders.csv` - seed order records
- `products.csv` - product catalog

## Typical Workflow

1. Install dependencies.
2. Configure SQL Server with `MSSQL_CONNECTION_STRING`.
3. Run `python3 train.py` if `data.pth` needs to be created.
4. Start the GUI with `python3 app.py` or the CLI with `python3 chat.py`.
