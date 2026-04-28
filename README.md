# E-commerce Chatbot

A Python chatbot for a CoffeeMugs e-commerce store. It can answer product questions, show available products, track orders, create orders, cancel orders, update delivery addresses, and let an admin update order status.

The project includes both a Tkinter GUI and a command-line chat interface.

## Features

- Intent classification with PyTorch
- Product catalog lookup from `products.csv`
- Content-based product recommendations using product attributes, browsing context, and cart/order context
- Product popularity analysis from saved database orders
- Simple market basket analysis for frequently bought product pairs from saved database orders
- Product category prediction using a small Naive Bayes ML model trained from `products.csv`
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

Recommendation examples:

```text
Recommend similar products
Recommend something like P001
Suggest products for my cart
Show me personalized recommendations
```

Analytics examples:

```text
Show product popularity
What are the top selling products?
Market basket analysis
Which products are frequently bought together?
```

Product category prediction examples:

```text
Predict category for P001
What category is P004?
Predict category for insulated travel mug
Classify product Classic Red Mug
```

## Test Responses

Run the response test script:

```bash
python3 generate_response.py
```

The script checks sample queries from `intents.json` and asks you to mark each generated response as correct or wrong.

## Evaluation And Experimentation

Run the automated evaluation script:

```bash
python evaluation.py
```

It reports:

- Chatbot intent accuracy and average prediction time
- Recommendation quality with Precision@3, hit rate, and mean reciprocal rank
- A comparison between chatbot behavior with and without the recommendation module
- User satisfaction survey averages from `evaluation_survey.csv`
- Product category prediction accuracy

## Project Structure

- `app.py` - Tkinter GUI entry point
- `chat.py` - command-line chatbot entry point
- `chatbot_engine.py` - intent model loading, prediction, and request routing helpers
- `chatbot_features.py` - shared chatbot feature responses for recommendations, analytics, and category prediction
- `product_catalog.py` - product CSV loading, formatting, and recommendation ranking
- `analytics.py` - product popularity and market basket analysis
- `category_predictor.py` - Naive Bayes product category prediction
- `db.py` - SQL Server setup and order/user database functions
- `model.py`, `nltk_utils.py`, `train.py` - PyTorch intent-classification training pipeline
- `evaluation.py`, `evaluation_survey.csv` - automated evaluation and survey metrics
- `generate_response.py`, `intent_response.py` - manual testing utilities
- `intents.json`, `data.pth` - chatbot intent data and trained model
- `products.csv`, `orders.csv` - product catalog and seed order records

## Typical Workflow

1. Install dependencies.
2. Configure SQL Server with `MSSQL_CONNECTION_STRING`.
3. Run `python3 train.py` if `data.pth` needs to be created.
4. Start the GUI with `python3 app.py` or the CLI with `python3 chat.py`.
